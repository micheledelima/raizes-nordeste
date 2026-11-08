import logging
from collections.abc import Callable
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.exceptions import HTTPException

from raizes.api.contratos import CadastroUsuario, Credenciais, RespostaErro, RespostaToken
from raizes.application.servicos import Contas
from raizes.domain.modelos import Ator, ErroNegocio

registrador = logging.getLogger("raizes")


def criar_api(contas: Contas) -> FastAPI:
    erros = {
        codigo: {"model": RespostaErro, "description": descricao}
        for codigo, descricao in {
            401: "Token ausente, invalido ou expirado.",
            403: "Perfil ou unidade sem permissao.",
            404: "Recurso inexistente.",
            409: "Conflito com regra de negocio.",
            422: "Contrato invalido.",
            503: "Dependencia temporariamente indisponivel.",
        }.items()
    }
    api = FastAPI(
        title="Raízes do Nordeste",
        version="0.1.0",
        description="Cadastro e autenticação de usuários.",
        responses=erros,
    )
    autenticacao_bearer = HTTPBearer(auto_error=False)

    @api.middleware("http")
    async def contexto_requisicao(requisicao: Request, proximo: Callable):
        requisicao.state.requisicao_id = str(uuid4())
        resposta = await proximo(requisicao)
        resposta.headers["X-Request-ID"] = requisicao.state.requisicao_id
        resposta.headers["Cache-Control"] = "no-store"
        return resposta

    def resposta_erro(requisicao, codigo, mensagem, status):
        cabecalhos = {"WWW-Authenticate": "Bearer"} if status == 401 else {}
        return JSONResponse(
            status_code=status,
            headers=cabecalhos,
            content={
                "erro": {
                    "codigo": codigo,
                    "mensagem": mensagem,
                    "requisicaoId": getattr(requisicao.state, "requisicao_id", str(uuid4())),
                }
            },
        )

    @api.exception_handler(ErroNegocio)
    async def erro_negocio(requisicao: Request, excecao: ErroNegocio):
        return resposta_erro(requisicao, excecao.codigo, excecao.mensagem, excecao.status)

    @api.exception_handler(RequestValidationError)
    async def erro_validacao(requisicao: Request, excecao: RequestValidationError):
        locais = {"body": "corpo", "query": "consulta", "path": "caminho", "header": "cabecalho"}
        campos = sorted(
            {
                ".".join(locais.get(str(parte), str(parte)) for parte in falha["loc"])
                for falha in excecao.errors()
            }
        )
        return resposta_erro(requisicao, "VALIDACAO", "Campos invalidos: " + ", ".join(campos), 422)

    @api.exception_handler(HTTPException)
    async def erro_http(requisicao: Request, excecao: HTTPException):
        return resposta_erro(
            requisicao, "HTTP_ERRO", "Recurso ou metodo indisponivel.", excecao.status_code
        )

    @api.exception_handler(Exception)
    async def erro_inesperado(requisicao: Request, excecao: Exception):
        registrador.error(
            "Falha interna requisicaoId=%s tipo=%s",
            requisicao.state.requisicao_id,
            type(excecao).__name__,
        )
        return resposta_erro(requisicao, "ERRO_INTERNO", "Falha interna.", 500)

    def ator_autenticado(
        credenciais: HTTPAuthorizationCredentials | None = Depends(autenticacao_bearer),
    ) -> Ator:
        if credenciais is None:
            raise ErroNegocio("NAO_AUTENTICADO", "Informe um token Bearer valido.", 401)
        return contas.autenticar(credenciais.credentials)

    @api.get("/healthcheck", tags=["Operacao"])
    def healthcheck():
        return {"status": "ok"}

    @api.post("/usuarios", status_code=201, tags=["Usuarios"], summary="Cadastrar cliente")
    def cadastrar(corpo: CadastroUsuario):
        return contas.cadastrar(corpo.nome, corpo.email, corpo.senha, corpo.consentimentoFidelidade)

    @api.post(
        "/autenticacao/entrar",
        response_model=RespostaToken,
        tags=["Autenticacao"],
        summary="Autenticar usuario",
    )
    def entrar(corpo: Credenciais):
        return contas.entrar(corpo.email, corpo.senha)

    @api.get("/usuarios/eu", tags=["Usuarios"], summary="Consultar dados do proprio usuario")
    def consultar_perfil(ator: Ator = Depends(ator_autenticado)):
        return contas.consultar_perfil(ator)

    return api
