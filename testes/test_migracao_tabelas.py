from raizes.infrastructure.banco_dados import BancoDados


def test_migracao_repetida_preserva_dados_e_integridade(tmp_path):
    banco = BancoDados(str(tmp_path / "persistencia.db"))
    banco.migrar()
    with banco.transacao() as repositorio:
        repositorio.adicionar("unidades", id="recife", nome="Recife", regiao="Pernambuco")
    banco.migrar()
    with banco.transacao() as repositorio:
        assert repositorio.obter("unidades", id="recife")["nome"] == "Recife"
        assert repositorio.contar("unidades") == 1
    conexao = banco.conectar()
    try:
        assert conexao.execute("PRAGMA foreign_key_check").fetchall() == []
        assert conexao.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conexao.execute("SELECT COUNT(*) FROM migracoes_esquema").fetchone()[0] == 1
    finally:
        conexao.close()
