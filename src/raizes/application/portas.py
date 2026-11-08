from contextlib import AbstractContextManager
from typing import Any, Protocol


class Repositorio(Protocol):
    def obter(self, tabela: str, **filtros: Any) -> dict | None: ...

    def listar(
        self, tabela: str, *, pagina: int = 1, limite: int = 100, **filtros: Any
    ) -> list[dict]: ...

    def contar(self, tabela: str, **filtros: Any) -> int: ...

    def adicionar(self, tabela: str, **valores: Any) -> dict: ...

    def atualizar(self, tabela: str, registro_id: str, **valores: Any) -> None: ...

    def ajustar_estoque(self, unidade_id: str, produto_id: str, variacao: int) -> None: ...


class UnidadeTrabalho(Protocol):
    def __call__(self) -> AbstractContextManager[Repositorio]: ...


class Seguranca(Protocol):
    def gerar_hash_senha(self, senha: str) -> str: ...

    def verificar_senha(self, senha: str, codificada: str) -> bool: ...

    def emitir_token(self, usuario_id: str) -> str: ...

    def ler_token(self, token: str) -> str: ...


def exigir_registro(repositorio: Repositorio, tabela: str, **filtros: Any) -> dict:
    from raizes.domain.modelos import ErroNegocio

    registro = repositorio.obter(tabela, **filtros)
    if registro is None:
        raise ErroNegocio("NAO_ENCONTRADO", "Recurso nao encontrado.", 404)
    return registro

def paginar(
    repositorio: Repositorio, tabela: str, pagina: int, limite: int, **filtros: Any
) -> dict:
    return {
        "itens": repositorio.listar(tabela, pagina=pagina, limite=limite, **filtros),
        "pagina": pagina,
        "limite": limite,
        "total": repositorio.contar(tabela, **filtros),
    }


class ServicoPagamento(Protocol):
    def solicitar(self, pedido_id: str, valor_centavos: int, resultado: str) -> dict: ...
