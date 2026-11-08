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


class CanalPedido(StrEnum):
    APP = "APP"
    TOTEM = "TOTEM"
    BALCAO = "BALCAO"
    PICKUP = "PICKUP"
    WEB = "WEB"


class StatusPedido(StrEnum):
    AGUARDANDO_PAGAMENTO = "AGUARDANDO_PAGAMENTO"
    EM_PREPARO = "EM_PREPARO"
    PRONTO = "PRONTO"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"

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

@dataclass(frozen=True)
class Pedido:
    status: StatusPedido
    total_centavos: int

    def alterar_status(self, destino: StatusPedido) -> None:
        permitidas = {
            StatusPedido.AGUARDANDO_PAGAMENTO: {StatusPedido.CANCELADO},
            StatusPedido.EM_PREPARO: {StatusPedido.PRONTO, StatusPedido.CANCELADO},
            StatusPedido.PRONTO: {StatusPedido.ENTREGUE},
        }
        if destino not in permitidas.get(self.status, set()):
            raise ErroNegocio("STATUS_INVALIDO", "Transicao de status nao permitida.")
