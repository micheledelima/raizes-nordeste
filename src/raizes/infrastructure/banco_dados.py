import sqlite3
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from raizes.domain.modelos import ErroNegocio

TABELAS = {
    "usuarios",
    "unidades",
    "produtos",
    "estoques",
    "pedidos",
    "itens_pedido",
    "pagamentos",
    "movimentacoes_estoque",
    "eventos_fidelidade",
    "consentimentos",
    "registros_auditoria",
}


class RepositorioSqlite:
    def __init__(self, conexao: sqlite3.Connection):
        self.conexao = conexao
        self.colunas = {
            tabela: {linha[1] for linha in conexao.execute(f"PRAGMA table_info({tabela})")}
            for tabela in TABELAS
        }

    def validar(self, tabela, valores):
        if tabela not in TABELAS or not set(valores).issubset(self.colunas[tabela]):
            raise ValueError("Tabela ou campos invalidos.")

    def condicao(self, tabela, filtros):
        self.validar(tabela, filtros)
        return " AND ".join(f"{chave} = ?" for chave in filtros) or "1 = 1"

    def obter(self, tabela, **filtros):
        linhas = self.listar(tabela, limite=1, **filtros)
        return linhas[0] if linhas else None

    def listar(self, tabela, *, pagina=1, limite=100, **filtros):
        clausula = self.condicao(tabela, filtros)
        linhas = self.conexao.execute(
            f"SELECT * FROM {tabela} WHERE {clausula} ORDER BY rowid LIMIT ? OFFSET ?",
            (*filtros.values(), limite, (pagina - 1) * limite),
        ).fetchall()
        return [dict(linha) for linha in linhas]

    def contar(self, tabela, **filtros):
        clausula = self.condicao(tabela, filtros)
        return self.conexao.execute(
            f"SELECT COUNT(*) FROM {tabela} WHERE {clausula}", tuple(filtros.values())
        ).fetchone()[0]

    def adicionar(self, tabela, **valores):
        valores = {"id": str(uuid4()), **valores}
        self.validar(tabela, valores)
        marcadores = ",".join("?" for _ in valores)
        self.conexao.execute(
            f"INSERT INTO {tabela} ({','.join(valores)}) VALUES ({marcadores})",
            tuple(valores.values()),
        )
        return self.obter(tabela, id=valores["id"])

    def atualizar(self, tabela, registro_id, **valores):
        self.validar(tabela, valores)
        atribuicoes = ",".join(f"{chave} = ?" for chave in valores)
        self.conexao.execute(
            f"UPDATE {tabela} SET {atribuicoes} WHERE id = ?", (*valores.values(), registro_id)
        )


class BancoDados:
    def __init__(self, caminho: str):
        self.caminho = caminho

    def conectar(self):
        Path(self.caminho).parent.mkdir(parents=True, exist_ok=True)
        conexao = sqlite3.connect(self.caminho, timeout=10, isolation_level=None)
        conexao.row_factory = sqlite3.Row
        conexao.execute("PRAGMA foreign_keys = ON")
        conexao.execute("PRAGMA busy_timeout = 10000")
        return conexao

    def migrar(self):
        conexao = self.conectar()
        try:
            conexao.execute("PRAGMA journal_mode = WAL")
            conexao.execute(
                "CREATE TABLE IF NOT EXISTS migracoes_esquema (versao TEXT PRIMARY KEY)"
            )
            for migracao in sorted(Path(__file__).with_name("migracoes").glob("*.sql")):
                if conexao.execute(
                    "SELECT 1 FROM migracoes_esquema WHERE versao = ?", (migracao.name,)
                ).fetchone():
                    continue
                versao = migracao.name.replace("'", "''")
                roteiro = "BEGIN IMMEDIATE;\n" + migracao.read_text(encoding="utf-8")
                roteiro += f"\nINSERT INTO migracoes_esquema VALUES ('{versao}'); COMMIT;"
                conexao.executescript(roteiro)
        except Exception:
            conexao.rollback()
            raise
        finally:
            conexao.close()

    @contextmanager
    def transacao(self):
        conexao = self.conectar()
        try:
            conexao.execute("BEGIN IMMEDIATE")
            yield RepositorioSqlite(conexao)
            conexao.commit()
        except sqlite3.IntegrityError as erro:
            conexao.rollback()
            raise ErroNegocio("CONFLITO", "Operacao viola uma restricao de integridade.") from erro
        except sqlite3.OperationalError as erro:
            conexao.rollback()
            raise ErroNegocio("BANCO_INDISPONIVEL", "Tente novamente mais tarde.", 503) from erro
        except Exception:
            conexao.rollback()
            raise
        finally:
            conexao.close()
