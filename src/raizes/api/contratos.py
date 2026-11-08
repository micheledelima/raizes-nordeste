from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from raizes.domain.modelos import CanalPedido, StatusPedido


class Contrato(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CadastroUsuario(Contrato):
    nome: str = Field(min_length=2, max_length=100, examples=["Maria Silva"])
    email: str = Field(
        min_length=5,
        max_length=254,
        pattern="^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$",
        examples=["maria@example.com"],
    )
    senha: str = Field(min_length=12, max_length=128, examples=["Senha-local-123!"])
    consentimentoFidelidade: bool = False

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor):
        return valor.lower()


class Credenciais(Contrato):
    email: str = Field(max_length=254)
    senha: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor):
        return valor.lower()


class CadastroUnidade(Contrato):
    nome: str = Field(min_length=2, max_length=100)
    regiao: str = Field(min_length=2, max_length=100)


class CadastroProduto(Contrato):
    nome: str = Field(min_length=2, max_length=100)
    precoCentavos: int = Field(gt=0, le=100000000, strict=True)


class MovimentacaoEstoque(Contrato):
    unidadeId: UUID
    produtoId: UUID
    quantidade: int = Field(ge=-1000000, le=1000000, strict=True)
    motivo: str = Field(min_length=3, max_length=200)

    @field_validator("quantidade")
    @classmethod
    def validar_quantidade(cls, valor):
        if valor == 0:
            raise ValueError("Quantidade deve ser diferente de zero.")
        return valor


class ItemPedido(Contrato):
    produtoId: UUID
    quantidade: int = Field(gt=0, le=1000, strict=True)


class CriacaoPedido(Contrato):
    unidadeId: UUID
    canalPedido: CanalPedido
    itens: list[ItemPedido] = Field(min_length=1, max_length=100)
    pontosResgate: int = Field(ge=0, le=100000000, strict=True, default=0)


class AlteracaoStatus(Contrato):
    status: StatusPedido


class ResultadoPagamento(StrEnum):
    APROVADO = "APROVADO"
    RECUSADO = "RECUSADO"
    TEMPO_ESGOTADO = "TEMPO_ESGOTADO"


class SolicitacaoPagamento(Contrato):
    pedidoId: UUID
    resultado: ResultadoPagamento = ResultadoPagamento.APROVADO


class AlteracaoConsentimento(Contrato):
    concedido: bool


class DetalheErro(BaseModel):
    codigo: str
    mensagem: str
    requisicaoId: str


class RespostaErro(BaseModel):
    erro: DetalheErro


class RespostaPedido(BaseModel):
    id: UUID
    clienteId: UUID
    unidadeId: UUID
    canalPedido: CanalPedido
    status: StatusPedido
    totalCentavos: int
    descontoCentavos: int
    pontosResgatados: int
    criadoEm: str
    itens: list[dict]


class Pagina(BaseModel):
    itens: list[dict]
    pagina: int
    limite: int
    total: int


class RespostaToken(BaseModel):
    tokenAcesso: str
    tipoToken: str


class RespostaPagamento(BaseModel):
    pagamento: dict
    pedido: RespostaPedido
