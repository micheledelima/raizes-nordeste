from copy import deepcopy

ID_UNIDADE = "10000000-0000-4000-8000-000000000001"
ID_PRODUTO = "20000000-0000-4000-8000-000000000001"
ID_PEDIDO = "40000000-0000-4000-8000-000000000001"
EXEMPLOS_ENTRADA = {
    "CadastroUsuario": {
        "nome": "Maria Silva",
        "email": "maria@example.com",
        "senha": "Senha-local-123!",
        "consentimentoFidelidade": True,
    },
    "Credenciais": {"email": "cliente@example.com", "senha": "senha-local-do-seed"},
    "CadastroUnidade": {"nome": "Recife Centro", "regiao": "Pernambuco"},
    "CadastroProduto": {"nome": "Tapioca de queijo", "precoCentavos": 1200},
    "MovimentacaoEstoque": {
        "unidadeId": ID_UNIDADE,
        "produtoId": ID_PRODUTO,
        "quantidade": 10,
        "motivo": "Reposicao",
    },
    "CriacaoPedido": {
        "unidadeId": ID_UNIDADE,
        "canalPedido": "TOTEM",
        "itens": [{"produtoId": ID_PRODUTO, "quantidade": 2}],
        "pontosResgate": 0,
    },
    "AlteracaoStatus": {"status": "PRONTO"},
    "SolicitacaoPagamento": {"pedidoId": ID_PEDIDO, "resultado": "APROVADO"},
    "AlteracaoConsentimento": {"concedido": True},
}
EXEMPLO_PEDIDO = {
    "id": ID_PEDIDO,
    "clienteId": "30000000-0000-4000-8000-000000000001",
    "unidadeId": ID_UNIDADE,
    "canalPedido": "TOTEM",
    "status": "AGUARDANDO_PAGAMENTO",
    "totalCentavos": 2400,
    "descontoCentavos": 0,
    "pontosResgatados": 0,
    "criadoEm": "2026-11-07T12:00:00+00:00",
    "itens": [],
}


def complementar_openapi(api):
    esquema = api.openapi()
    for metodos in esquema["paths"].values():
        for operacao in metodos.values():
            corpo = operacao.get("requestBody", {}).get("content", {}).get("application/json")
            if corpo:
                nome = corpo["schema"].get("$ref", "").split("/")[-1]
                if nome in EXEMPLOS_ENTRADA:
                    corpo["example"] = EXEMPLOS_ENTRADA[nome]
            for codigo, resposta in operacao["responses"].items():
                conteudo = resposta.get("content", {}).get("application/json")
                if not conteudo:
                    continue
                referencia = conteudo.get("schema", {}).get("$ref", "").split("/")[-1]
                if referencia == "RespostaPedido":
                    exemplo = deepcopy(EXEMPLO_PEDIDO)
                    if operacao.get("operationId", "").startswith("atualizar_status"):
                        exemplo["status"] = "PRONTO"
                    conteudo["example"] = exemplo
                elif referencia == "RespostaToken":
                    conteudo["example"] = {"tokenAcesso": "jwt", "tipoToken": "bearer"}
                elif referencia == "Pagina":
                    conteudo["example"] = {"itens": [], "pagina": 1, "limite": 10, "total": 0}
                if int(codigo) >= 400:
                    conteudo["example"] = {
                        "erro": {
                            "codigo": "VALIDACAO" if codigo == "422" else "REGRA_DE_NEGOCIO",
                            "mensagem": "Verifique os dados e as permissoes da operacao.",
                            "requisicaoId": "uuid",
                        }
                    }
    return api
