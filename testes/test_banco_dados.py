import pytest

from raizes.domain.modelos import ErroNegocio
from raizes.infrastructure.banco_dados import BancoDados


@pytest.fixture
def banco(tmp_path):
    instancia = BancoDados(str(tmp_path / "dados" / "teste.db"))
    instancia.migrar()
    return instancia


def test_cria_banco_e_esquema(banco):
    conexao = banco.conectar()
    try:
        tabelas = {
            linha[0]
            for linha in conexao.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        assert {
            "usuarios",
            "unidades",
            "produtos",
            "estoques",
            "pedidos",
            "itens_pedido",
            "pagamentos",
            "consentimentos",
            "registros_auditoria",
            "eventos_fidelidade",
            "movimentacoes_estoque",
            "migracoes_esquema",
        } == tabelas
        assert conexao.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        conexao.close()


def test_transacao_persiste_registro(banco):
    with banco.transacao() as repositorio:
        unidade = repositorio.adicionar("unidades", nome="Recife", regiao="Pernambuco")
    with banco.transacao() as repositorio:
        assert repositorio.obter("unidades", id=unidade["id"])["nome"] == "Recife"


def test_falha_desfaz_transacao(banco):
    with pytest.raises(ValueError, match="Falha simulada"):
        with banco.transacao() as repositorio:
            repositorio.adicionar("unidades", nome="Recife", regiao="Pernambuco")
            raise ValueError("Falha simulada")
    with banco.transacao() as repositorio:
        assert repositorio.contar("unidades") == 0


def test_rejeita_referencia_inexistente(banco):
    with pytest.raises(ErroNegocio) as falha:
        with banco.transacao() as repositorio:
            repositorio.adicionar("estoques", unidade_id="inexistente", produto_id="inexistente")
    assert falha.value.codigo == "CONFLITO"
    with banco.transacao() as repositorio:
        assert repositorio.contar("estoques") == 0


def test_rejeita_saldo_negativo(banco):
    with pytest.raises(ErroNegocio):
        with banco.transacao() as repositorio:
            unidade = repositorio.adicionar("unidades", nome="Recife", regiao="Pernambuco")
            produto = repositorio.adicionar("produtos", nome="Tapioca", preco_centavos=1200)
            repositorio.adicionar(
                "estoques", unidade_id=unidade["id"], produto_id=produto["id"], quantidade=-1
            )


def test_reaplicacao_nao_duplica_versao(banco):
    banco.migrar()
    conexao = banco.conectar()
    try:
        assert (
            conexao.execute("SELECT versao FROM migracoes_esquema").fetchall()[0][0]
            == "001_inicial.sql"
        )
        assert conexao.execute("SELECT COUNT(*) FROM migracoes_esquema").fetchone()[0] == 1
    finally:
        conexao.close()
