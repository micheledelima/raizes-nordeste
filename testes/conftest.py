import pytest
from fastapi.testclient import TestClient

from raizes.api.rotas import criar_api
from raizes.application.servicos import Catalogo, Contas, GestaoPedidos
from raizes.infrastructure.banco_dados import BancoDados
from raizes.infrastructure.dados_iniciais import popular
from raizes.infrastructure.pagamentos import PagamentoSimulado
from raizes.infrastructure.seguranca import SegurancaJwt

SENHA = "Teste-local-123!"


@pytest.fixture
def api(tmp_path):
    banco = BancoDados(str(tmp_path / "teste.db"))
    banco.migrar()
    seguranca = SegurancaJwt("segredo-testes-com-pelo-menos-32-caracteres")
    popular(banco, seguranca, SENHA)
    api = criar_api(
        Contas(banco.transacao, seguranca),
        Catalogo(banco.transacao),
        GestaoPedidos(banco.transacao, PagamentoSimulado()),
    )
    with TestClient(api) as cliente:
        yield (cliente, banco)


@pytest.fixture
def autenticacao(api):
    cliente, _ = api

    def entrar(perfil="cliente"):
        resultado = cliente.post(
            "/autenticacao/entrar", json={"email": f"{perfil}@example.com", "senha": SENHA}
        )
        assert resultado.status_code == 200
        return {"Authorization": f"Bearer {resultado.json()['tokenAcesso']}"}

    return entrar
