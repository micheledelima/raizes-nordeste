from pydantic import BaseModel, ConfigDict, Field, field_validator


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


class DetalheErro(BaseModel):
    codigo: str
    mensagem: str
    requisicaoId: str


class RespostaErro(BaseModel):
    erro: DetalheErro


class RespostaToken(BaseModel):
    tokenAcesso: str
    tipoToken: str
