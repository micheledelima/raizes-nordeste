from raizes.api.rotas import criar_api
from raizes.application.servicos import Catalogo, Contas, GestaoPedidos
from raizes.configuracao import Configuracoes
from raizes.infrastructure.banco_dados import BancoDados
from raizes.infrastructure.pagamentos import PagamentoSimulado
from raizes.infrastructure.seguranca import SegurancaJwt


def montar_api():
    configuracoes = Configuracoes.do_ambiente()
    banco = BancoDados(configuracoes.banco)
    seguranca = SegurancaJwt(configuracoes.segredo_jwt, configuracoes.duracao_token_minutos)
    return criar_api(
        Contas(banco.transacao, seguranca),
        Catalogo(banco.transacao),
        GestaoPedidos(banco.transacao, PagamentoSimulado()),
    )
