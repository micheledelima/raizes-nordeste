from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from raizes.api.rotas import criar_api
from raizes.application.servicos import Catalogo, Contas, GestaoPedidos
from raizes.infrastructure.banco_dados import BancoDados
from raizes.infrastructure.dados_iniciais import PRODUTO_TAPIOCA, UNIDADE_RECIFE, popular
from raizes.infrastructure.pagamentos import PagamentoSimulado
from raizes.infrastructure.seguranca import SegurancaJwt

SENHA = "Teste-local-123!"


@pytest.fixture
def api(tmp_path):
    banco = BancoDados(str(tmp_path / "teste.db"))
    banco.migrar()
    seguranca = SegurancaJwt("segredo-testes-com-pelo-menos-32-caracteres")
    popular(banco, seguranca, SENHA)
    aplicacao = criar_api(
        Contas(banco.transacao, seguranca),
        Catalogo(banco.transacao),
        GestaoPedidos(banco.transacao, PagamentoSimulado()),
    )
    with TestClient(aplicacao) as cliente:
        yield cliente, banco


def autenticacao(cliente, perfil="cliente"):
    resposta = cliente.post(
        "/autenticacao/entrar", json={"email": f"{perfil}@example.com", "senha": SENHA}
    )
    assert resposta.status_code == 200
    return {"Authorization": f"Bearer {resposta.json()['tokenAcesso']}"}


def criar_pedido(cliente, cabecalhos):
    return cliente.post(
        "/pedidos",
        headers={**cabecalhos, "Idempotency-Key": str(uuid4())},
        json={
            "unidadeId": UNIDADE_RECIFE,
            "canalPedido": "TOTEM",
            "itens": [{"produtoId": PRODUTO_TAPIOCA, "quantidade": 2}],
        },
    )


def test_cria_pedido_multicanal_e_reserva_estoque(api):
    cliente, banco = api
    cabecalhos = autenticacao(cliente)
    resposta = criar_pedido(cliente, cabecalhos)
    assert resposta.status_code == 201
    pedido = resposta.json()
    assert pedido["canalPedido"] == "TOTEM"
    assert pedido["totalCentavos"] == 2400
    assert cliente.get("/pedidos?canalPedido=TOTEM", headers=cabecalhos).json()["total"] == 1
    with banco.transacao() as repositorio:
        estoque = repositorio.obter("estoques", unidade_id=UNIDADE_RECIFE, produto_id=PRODUTO_TAPIOCA)
        assert estoque["quantidade"] == 98


def test_pagamento_aprovado_e_fluxo_de_entrega(api):
    cliente, _ = api
    cliente_autenticado = autenticacao(cliente)
    pedido = criar_pedido(cliente, cliente_autenticado).json()
    pagamento = cliente.post(
        "/pagamentos",
        headers=cliente_autenticado,
        json={"pedidoId": pedido["id"], "resultado": "APROVADO"},
    )
    assert pagamento.status_code == 201
    assert pagamento.json()["pedido"]["status"] == "EM_PREPARO"
    assert cliente.patch(
        f"/pedidos/{pedido['id']}/status",
        headers=autenticacao(cliente, "cozinha"),
        json={"status": "PRONTO"},
    ).status_code == 200
    assert cliente.patch(
        f"/pedidos/{pedido['id']}/status",
        headers=autenticacao(cliente, "atendente"),
        json={"status": "ENTREGUE"},
    ).status_code == 200


def test_pagamento_recusado_devolve_estoque(api):
    cliente, banco = api
    cabecalhos = autenticacao(cliente)
    pedido = criar_pedido(cliente, cabecalhos).json()
    resposta = cliente.post(
        "/pagamentos",
        headers=cabecalhos,
        json={"pedidoId": pedido["id"], "resultado": "RECUSADO"},
    )
    assert resposta.status_code == 201
    assert resposta.json()["pedido"]["status"] == "CANCELADO"
    with banco.transacao() as repositorio:
        estoque = repositorio.obter("estoques", unidade_id=UNIDADE_RECIFE, produto_id=PRODUTO_TAPIOCA)
        assert estoque["quantidade"] == 100


def test_perfil_sem_permissao_nao_altera_status(api):
    cliente, _ = api
    cliente_autenticado = autenticacao(cliente)
    pedido = criar_pedido(cliente, cliente_autenticado).json()
    cliente.post(
        "/pagamentos",
        headers=cliente_autenticado,
        json={"pedidoId": pedido["id"], "resultado": "APROVADO"},
    )
    resposta = cliente.patch(
        f"/pedidos/{pedido['id']}/status",
        headers=cliente_autenticado,
        json={"status": "PRONTO"},
    )
    assert resposta.status_code == 403
