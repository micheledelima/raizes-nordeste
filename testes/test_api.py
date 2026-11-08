from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from raizes.infrastructure.dados_iniciais import (
    PRODUTO_CUSCUZ,
    PRODUTO_TAPIOCA,
    UNIDADE_NATAL,
    UNIDADE_RECIFE,
)


def retorno(canal="APP", quantidade=2, produto=PRODUTO_TAPIOCA):
    return {
        "unidadeId": UNIDADE_RECIFE,
        "canalPedido": canal,
        "itens": [{"produtoId": produto, "quantidade": quantidade}],
    }


def criar(cliente, cabecalhos, corpo=None, chave=None):
    return cliente.post(
        "/pedidos",
        headers={**cabecalhos, "Idempotency-Key": chave or str(uuid4())},
        json=corpo or retorno(),
    )


def test_t01_autenticacao_e_perfil(api, autenticacao):
    cliente, _ = api
    resultado = cliente.get("/usuarios/eu", headers=autenticacao())
    assert resultado.status_code == 200
    assert resultado.json()["perfil"] == "CLIENTE"
    assert "senha_hash" not in resultado.json()


def test_t02_cardapio_publico(api):
    cliente, _ = api
    resultado = cliente.get(f"/unidades/{UNIDADE_RECIFE}/cardapio")
    assert resultado.status_code == 200
    assert resultado.json()["total"] == 2


def test_t03_criacao_filtro_e_persistencia(api, autenticacao):
    cliente, banco = api
    cabecalhos = autenticacao()
    resultado = criar(cliente, cabecalhos, retorno("TOTEM"))
    assert resultado.status_code == 201
    pedido = resultado.json()
    assert pedido["totalCentavos"] == 2400
    assert pedido["canalPedido"] == "TOTEM"
    assert cliente.get("/pedidos?canalPedido=TOTEM", headers=cabecalhos).json()["total"] == 1
    assert cliente.get("/pedidos?canalPedido=WEB", headers=cabecalhos).json()["total"] == 0
    with banco.transacao() as repositorio:
        assert repositorio.obter("pedidos", id=pedido["id"])
        assert (
            repositorio.obter("estoques", unidade_id=UNIDADE_RECIFE, produto_id=PRODUTO_TAPIOCA)[
                "quantidade"
            ]
            == 98
        )


def test_t04_pagamento_entrega_e_credito_unico(api, autenticacao):
    cliente, _ = api
    cliente_autenticado = autenticacao()
    pedido = criar(cliente, cliente_autenticado).json()
    pagamento = cliente.post(
        "/pagamentos",
        headers=cliente_autenticado,
        json={"pedidoId": pedido["id"], "resultado": "APROVADO"},
    )
    assert pagamento.status_code == 201
    assert pagamento.json()["pedido"]["status"] == "EM_PREPARO"
    assert (
        cliente.patch(
            f"/pedidos/{pedido['id']}/status",
            headers=autenticacao("cozinha"),
            json={"status": "PRONTO"},
        ).status_code
        == 200
    )
    assert (
        cliente.patch(
            f"/pedidos/{pedido['id']}/status",
            headers=autenticacao("atendente"),
            json={"status": "ENTREGUE"},
        ).status_code
        == 200
    )
    assert cliente.get("/fidelidade", headers=cliente_autenticado).json()["saldo"] == 24
    assert (
        cliente.patch(
            f"/pedidos/{pedido['id']}/status",
            headers=autenticacao("atendente"),
            json={"status": "ENTREGUE"},
        ).status_code
        == 409
    )
    assert cliente.get("/fidelidade", headers=cliente_autenticado).json()["saldo"] == 24


def test_t05_pagamento_recusado_devolve_estoque(api, autenticacao):
    cliente, banco = api
    cabecalhos = autenticacao()
    pedido = criar(cliente, cabecalhos).json()
    resultado = cliente.post(
        "/pagamentos", headers=cabecalhos, json={"pedidoId": pedido["id"], "resultado": "RECUSADO"}
    )
    assert resultado.status_code == 201
    assert resultado.json()["pedido"]["status"] == "CANCELADO"
    with banco.transacao() as repositorio:
        assert (
            repositorio.obter("estoques", unidade_id=UNIDADE_RECIFE, produto_id=PRODUTO_TAPIOCA)[
                "quantidade"
            ]
            == 100
        )


def test_t06_estoque_e_auditoria(api, autenticacao):
    cliente, _ = api
    administrador = autenticacao("admin")
    corpo = {
        "unidadeId": UNIDADE_RECIFE,
        "produtoId": PRODUTO_TAPIOCA,
        "quantidade": 5,
        "motivo": "Reposicao",
    }
    resultado = cliente.post("/estoques/movimentacoes", headers=administrador, json=corpo)
    assert resultado.status_code == 201
    assert resultado.json()["quantidade"] == 105
    auditar = cliente.get("/auditorias", headers=administrador)
    assert any(item["acao"] == "ESTOQUE_MOVIMENTADO" for item in auditar.json()["itens"])


def test_t07_acesso_sem_token(api):
    cliente, _ = api
    resultado = cliente.get("/pedidos")
    assert resultado.status_code == 401
    assert resultado.json()["erro"]["codigo"] == "NAO_AUTENTICADO"
    assert resultado.headers["www-authenticate"] == "Bearer"


def test_t08_perfil_sem_permissao(api, autenticacao):
    cliente, _ = api
    assert cliente.get(f"/estoques/{UNIDADE_RECIFE}", headers=autenticacao()).status_code == 403


@pytest.mark.parametrize(
    "alteracao", ["canal_ausente", "canal_invalido", "quantidade_negativa", "campo_desconhecido"]
)
def test_t09_validacao(api, autenticacao, alteracao):
    cliente, _ = api
    corpo = retorno()
    if alteracao == "canal_ausente":
        corpo.pop("canalPedido")
    elif alteracao == "canal_invalido":
        corpo["canalPedido"] = "OUTRO"
    elif alteracao == "quantidade_negativa":
        corpo["itens"][0]["quantidade"] = -1
    else:
        corpo["totalCentavos"] = 1
    resultado = criar(cliente, autenticacao(), corpo)
    assert resultado.status_code == 422
    assert resultado.json()["erro"]["codigo"] == "VALIDACAO"


def test_t10_produto_inexistente(api, autenticacao):
    cliente, _ = api
    assert criar(cliente, autenticacao(), retorno(produto=str(uuid4()))).status_code == 404


def test_t11_estoque_insuficiente_desfaz_pedido(api, autenticacao):
    cliente, banco = api
    corpo = retorno(quantidade=1)
    corpo["itens"].append({"produtoId": PRODUTO_CUSCUZ, "quantidade": 101})
    assert criar(cliente, autenticacao(), corpo).status_code == 409
    with banco.transacao() as repositorio:
        assert repositorio.contar("pedidos") == 0
        assert (
            repositorio.obter("estoques", unidade_id=UNIDADE_RECIFE, produto_id=PRODUTO_TAPIOCA)[
                "quantidade"
            ]
            == 100
        )


def test_t12_idempotencia_pedido_e_pagamento(api, autenticacao):
    cliente, banco = api
    cabecalhos = autenticacao()
    primeiro = criar(cliente, cabecalhos, chave="same-key-123").json()
    segundo = criar(cliente, cabecalhos, chave="same-key-123").json()
    assert primeiro["id"] == segundo["id"]
    assert (
        criar(cliente, cabecalhos, retorno(quantidade=3), chave="same-key-123").status_code == 409
    )
    for _ in range(2):
        assert (
            cliente.post(
                "/pagamentos",
                headers=cabecalhos,
                json={"pedidoId": primeiro["id"], "resultado": "APROVADO"},
            ).status_code
            == 201
        )
    with banco.transacao() as repositorio:
        assert repositorio.contar("pedidos") == 1
        assert repositorio.contar("pagamentos") == 1
        assert (
            repositorio.obter("estoques", unidade_id=UNIDADE_RECIFE, produto_id=PRODUTO_TAPIOCA)[
                "quantidade"
            ]
            == 98
        )


def test_t13_tempo_esgotado_permite_nova_tentativa(api, autenticacao):
    cliente, banco = api
    cabecalhos = autenticacao()
    pedido = criar(cliente, cabecalhos).json()
    assert (
        cliente.post(
            "/pagamentos",
            headers=cabecalhos,
            json={"pedidoId": pedido["id"], "resultado": "TEMPO_ESGOTADO"},
        ).status_code
        == 503
    )
    with banco.transacao() as repositorio:
        assert repositorio.contar("pagamentos") == 0
        assert repositorio.obter("pedidos", id=pedido["id"])["status"] == "AGUARDANDO_PAGAMENTO"
    assert (
        cliente.post(
            "/pagamentos",
            headers=cabecalhos,
            json={"pedidoId": pedido["id"], "resultado": "APROVADO"},
        ).status_code
        == 201
    )


def test_t14_isolamento_unidades(api, autenticacao):
    cliente, _ = api
    gerente = autenticacao("gerente")
    assert cliente.get(f"/estoques/{UNIDADE_NATAL}", headers=gerente).status_code == 403


def test_t15_isolamento_usuarios(api, autenticacao):
    cliente, _ = api
    pedido = criar(cliente, autenticacao()).json()
    assert (
        cliente.post(
            "/usuarios",
            json={
                "nome": "Outro Cliente",
                "email": "outro@example.com",
                "senha": "Teste-local-123!",
            },
        ).status_code
        == 201
    )
    entrar = cliente.post(
        "/autenticacao/entrar", json={"email": "outro@example.com", "senha": "Teste-local-123!"}
    ).json()
    cabecalhos = {"Authorization": "Bearer " + entrar["tokenAcesso"]}
    assert cliente.get(f"/pedidos/{pedido['id']}", headers=cabecalhos).status_code == 403
    assert cliente.get("/pedidos", headers=cabecalhos).json()["total"] == 0


def test_t16_consentimento_e_anonimizacao(api, autenticacao):
    cliente, _ = api
    cabecalhos = autenticacao()
    assert (
        cliente.put(
            "/usuarios/eu/consentimentos", headers=cabecalhos, json={"concedido": False}
        ).status_code
        == 200
    )
    corpo = {**retorno(), "pontosResgate": 1}
    assert criar(cliente, cabecalhos, corpo).status_code == 409
    assert cliente.delete("/usuarios/eu", headers=cabecalhos).status_code == 204
    assert cliente.get("/usuarios/eu", headers=cabecalhos).status_code == 401


def test_t17_itens_repetidos_somados_antes_da_reserva(api, autenticacao):
    cliente, banco = api
    corpo = retorno(quantidade=60)
    corpo["itens"].append({"produtoId": PRODUTO_TAPIOCA, "quantidade": 60})
    assert criar(cliente, autenticacao(), corpo).status_code == 409
    with banco.transacao() as repositorio:
        assert repositorio.contar("pedidos") == 0


def test_t18_pedidos_concorrentes_respeitam_estoque(api, autenticacao):
    cliente, banco = api
    cabecalhos = autenticacao()
    with ThreadPoolExecutor(max_workers=2) as executor:
        codigos = list(
            executor.map(
                lambda _: criar(cliente, cabecalhos, retorno(quantidade=80)).status_code, range(2)
            )
        )
    assert sorted(codigos) == [201, 409]
    with banco.transacao() as repositorio:
        assert (
            repositorio.obter("estoques", unidade_id=UNIDADE_RECIFE, produto_id=PRODUTO_TAPIOCA)[
                "quantidade"
            ]
            == 20
        )


def test_t19_cancelamento_devolve_pontos_e_estorna_pagamento(api, autenticacao):
    cliente, banco = api
    cliente_autenticado = autenticacao()
    with banco.transacao() as repositorio:
        usuario = repositorio.obter("usuarios", email="cliente@example.com")
        repositorio.ajustar_pontos(usuario["id"], 100)
    pedido = criar(cliente, cliente_autenticado, {**retorno(), "pontosResgate": 50}).json()
    assert pedido["totalCentavos"] == 2350
    cliente.post(
        "/pagamentos",
        headers=cliente_autenticado,
        json={"pedidoId": pedido["id"], "resultado": "APROVADO"},
    )
    assert (
        cliente.patch(
            f"/pedidos/{pedido['id']}/status",
            headers=autenticacao("gerente"),
            json={"status": "CANCELADO"},
        ).status_code
        == 200
    )
    assert cliente.get("/fidelidade", headers=cliente_autenticado).json()["saldo"] == 100
    with banco.transacao() as repositorio:
        assert repositorio.obter("pagamentos", pedido_id=pedido["id"])["status"] == "ESTORNADO"


def test_t20_credenciais_e_token_invalidos(api):
    cliente, _ = api
    assert (
        cliente.post(
            "/autenticacao/entrar", json={"email": "cliente@example.com", "senha": "errada"}
        ).status_code
        == 401
    )
    assert cliente.get("/pedidos", headers={"Authorization": "Bearer invalid"}).status_code == 401


def test_t21_contrato_saude_e_erro_padrao(api):
    cliente, _ = api
    assert cliente.get("/healthcheck").json() == {"status": "ok"}
    assert cliente.get("/docs").status_code == 200
    assert "canalPedido" in cliente.get("/openapi.json").text
    assert "erro" in cliente.get("/nao-existe").json()


def test_t22_migracoes_e_dados_iniciais_repetiveis(api):
    from raizes.infrastructure.dados_iniciais import popular
    from raizes.infrastructure.seguranca import SegurancaJwt

    _, banco = api
    banco.migrar()
    popular(banco, SegurancaJwt("segredo-testes-com-pelo-menos-32-caracteres"), "Teste-local-123!")
    with banco.transacao() as repositorio:
        assert repositorio.contar("usuarios") == 5
        assert repositorio.contar("estoques") == 4


def test_contratos_e_paginacao_em_portugues(api):
    cliente, _ = api
    resposta = cliente.get("/unidades?pagina=2&limite=1")
    assert resposta.status_code == 200
    assert set(resposta.json()) == {"itens", "pagina", "limite", "total"}
    assert resposta.json()["pagina"] == 2
    assert resposta.json()["limite"] == 1
    assert resposta.json()["itens"][0]["id"] == UNIDADE_NATAL
    produtos = cliente.get("/produtos").json()["itens"]
    assert {"nome", "preco_centavos", "ativo"}.issubset(produtos[0])
    assert not {"name", "price_cents", "active"}.intersection(produtos[0])
    falha = cliente.get("/pedidos")
    assert falha.json()["erro"]["requisicaoId"] == falha.headers["X-Request-ID"]
    esquema = cliente.get("/openapi.json").json()
    assert "/autenticacao/entrar" in esquema["paths"]
    propriedades = esquema["components"]["schemas"]["RespostaToken"]["properties"]
    assert set(propriedades) == {"tokenAcesso", "tipoToken"}
    assert "TEMPO_ESGOTADO" in esquema["components"]["schemas"]["ResultadoPagamento"]["enum"]
