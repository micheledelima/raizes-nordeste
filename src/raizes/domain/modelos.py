from dataclasses import dataclass
from enum import StrEnum


class ErroNegocio(Exception):
    def __init__(self, codigo: str, mensagem: str, status: int = 409):
        self.codigo = codigo
        self.mensagem = mensagem
        self.status = status
        super().__init__(mensagem)


class Perfil(StrEnum):
    CLIENTE = "CLIENTE"
    ATENDENTE = "ATENDENTE"
    COZINHA = "COZINHA"
    GERENTE = "GERENTE"
    ADMIN = "ADMIN"


@dataclass(frozen=True)
class Ator:
    id: str
    perfil: Perfil
    unidade_id: str | None

    def exigir(self, *perfis: Perfil) -> None:
        if self.perfil not in perfis:
            raise ErroNegocio("SEM_PERMISSAO", "Perfil sem permissao para esta operacao.", 403)

    def verificar_unidade(self, unidade_id: str) -> None:
        if self.perfil != Perfil.ADMIN and self.unidade_id != unidade_id:
            raise ErroNegocio("SEM_PERMISSAO", "Usuario sem acesso a esta unidade.", 403)
