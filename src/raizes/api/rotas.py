import logging
from collections.abc import Callable
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.exceptions import HTTPException

from raizes.api.contratos import (
    AlteracaoStatus,
    CadastroProduto,
    CadastroUnidade,
    CadastroUsuario,
    Credenciais,
    CriacaoPedido,
    MovimentacaoEstoque,
    Pagina,
    RespostaErro,
    RespostaPagamento,
    RespostaPedido,
    RespostaToken,
    SolicitacaoPagamento,
)
from raizes.application.servicos import Catalogo, Contas, GestaoPedidos
from raizes.domain.modelos import Ator, CanalPedido, ErroNegocio, StatusPedido

registrador = logging.getLogger("raizes")


def criar_api(contas: Contas, catalogo: Catalogo, gestao_pedidos: GestaoPedidos) -> FastAPI:
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

    @api.get(
        "/unidades", response_model=Pagina, tags=["Unidades"], summary="Listar unidades ativas"
    )
    def listar_unidades(pagina: int = Query(1, ge=1), limite: int = Query(10, ge=1, le=100)):
        return catalogo.listar_unidades(pagina, limite)

    @api.post(
        "/unidades",
        status_code=201,
        tags=["Unidades"],
        summary="Cadastrar unidade como administrador",
    )
    def cadastrar_unidade(corpo: CadastroUnidade, ator: Ator = Depends(ator_autenticado)):
        return catalogo.cadastrar_unidade(ator, corpo.nome, corpo.regiao)

    @api.get(
        "/produtos", response_model=Pagina, tags=["Produtos"], summary="Listar produtos ativos"
    )
    def listar_produtos(pagina: int = Query(1, ge=1), limite: int = Query(10, ge=1, le=100)):
        return catalogo.listar_produtos(pagina, limite)

    @api.post(
        "/produtos",
        status_code=201,
        tags=["Produtos"],
        summary="Cadastrar produto como administrador",
    )
    def cadastrar_produto(corpo: CadastroProduto, ator: Ator = Depends(ator_autenticado)):
        return catalogo.cadastrar_produto(ator, corpo.nome, corpo.precoCentavos)

    @api.get(
        "/unidades/{unidade_id}/cardapio",
        response_model=Pagina,
        tags=["Produtos"],
        summary="Consultar cardapio e disponibilidade da unidade",
    )
    def cardapio(
        unidade_id: UUID, pagina: int = Query(1, ge=1), limite: int = Query(10, ge=1, le=100)
    ):
        return catalogo.cardapio(str(unidade_id), pagina, limite)

    @api.get(
        "/estoques/{unidade_id}",
        response_model=Pagina,
        tags=["Estoques"],
        summary="Consultar estoque como gerente da unidade ou administrador",
    )
    def consultar_estoque(
        unidade_id: UUID,
        pagina: int = Query(1, ge=1),
        limite: int = Query(10, ge=1, le=100),
        ator: Ator = Depends(ator_autenticado),
    ):
        return catalogo.consultar_estoque(ator, str(unidade_id), pagina, limite)

    @api.post(
        "/estoques/movimentacoes",
        status_code=201,
        tags=["Estoques"],
        summary="Movimentar estoque como gerente da unidade ou administrador",
    )
    def movimentar_estoque(corpo: MovimentacaoEstoque, ator: Ator = Depends(ator_autenticado)):
        return catalogo.movimentar_estoque(
            ator, str(corpo.unidadeId), str(corpo.produtoId), corpo.quantidade, corpo.motivo
        )


    @api.post(
        "/pedidos",
        status_code=201,
        response_model=RespostaPedido,
        tags=["Pedidos"],
        summary="Criar pedido com reserva de estoque",
        description="CLIENTE: pedidos proprios. ATENDENTE: unidade vinculada. ADMIN: qualquer unidade. Idempotency-Key obrigatoria; repetir a mesma chave e conteudo devolve o mesmo pedido.",
    )
    def criar_pedido(
        corpo: CriacaoPedido,
        chave_idempotencia: str = Header(alias="Idempotency-Key", min_length=8, max_length=100),
        ator: Ator = Depends(ator_autenticado),
    ):
        itens = [
            {"produtoId": str(item.produtoId), "quantidade": item.quantidade}
            for item in corpo.itens
        ]
        return gestao_pedidos.criar(
            ator,
            str(corpo.unidadeId),
            corpo.canalPedido,
            itens,
            chave_idempotencia,
        )

    @api.get(
        "/pedidos",
        response_model=Pagina,
        tags=["Pedidos"],
        summary="Listar pedidos com isolamento por cliente ou unidade",
    )
    def listar_pedidos(
        pagina: int = Query(1, ge=1),
        limite: int = Query(10, ge=1, le=100),
        canalPedido: CanalPedido | None = None,
        status: StatusPedido | None = None,
        ator: Ator = Depends(ator_autenticado),
    ):
        return gestao_pedidos.listar(ator, pagina, limite, canalPedido, status)

    @api.get(
        "/pedidos/{pedido_id}",
        response_model=RespostaPedido,
        tags=["Pedidos"],
        summary="Consultar pedido proprio ou da unidade",
    )
    def consultar_pedido(pedido_id: UUID, ator: Ator = Depends(ator_autenticado)):
        return gestao_pedidos.obter(ator, str(pedido_id))

    @api.patch(
        "/pedidos/{pedido_id}/status",
        response_model=RespostaPedido,
        tags=["Pedidos"],
        summary="Atualizar status respeitando o fluxo operacional",
        description="PRONTO: cozinha, gerente ou admin. ENTREGUE: atendente, gerente ou admin. CANCELADO: cliente antes do pagamento; atendente, gerente ou admin antes de pronto. Funcionarios restritos a unidade vinculada.",
    )
    def atualizar_status(
        pedido_id: UUID, corpo: AlteracaoStatus, ator: Ator = Depends(ator_autenticado)
    ):
        return gestao_pedidos.alterar_status(ator, str(pedido_id), corpo.status)

    @api.post(
        "/pagamentos",
        status_code=201,
        response_model=RespostaPagamento,
        tags=["Pagamentos"],
        summary="Solicitar e registrar pagamento mock",
        description="CLIENTE proprietario, ATENDENTE da unidade ou ADMIN. APROVADO inicia preparo; RECUSADO cancela e devolve estoque; TEMPO_ESGOTADO retorna 503 sem finalizar. Repeticao do mesmo resultado nao duplica pagamento.",
    )
    def pagar(corpo: SolicitacaoPagamento, ator: Ator = Depends(ator_autenticado)):
        return gestao_pedidos.pagar(ator, str(corpo.pedidoId), corpo.resultado)


    return api
