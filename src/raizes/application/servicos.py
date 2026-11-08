import hashlib
import json
from collections import Counter
from datetime import UTC, datetime

from raizes.application.portas import (
    Seguranca,
    ServicoPagamento,
    UnidadeTrabalho,
    exigir_registro,
    paginar,
)
from raizes.domain.modelos import Ator, ErroNegocio, Pedido, Perfil, StatusPedido


def agora() -> str:
    return datetime.now(UTC).isoformat()


def auditar(repositorio, ator: Ator, acao: str, recurso_id: str):
    repositorio.adicionar(
        "registros_auditoria", ator_id=ator.id, acao=acao, recurso_id=recurso_id, criado_em=agora()
    )


class Contas:
    def __init__(self, unidade_trabalho: UnidadeTrabalho, seguranca: Seguranca):
        self.unidade_trabalho = unidade_trabalho
        self.seguranca = seguranca

    def cadastrar(self, nome, email, senha, consentimento=False):
        codificada = self.seguranca.gerar_hash_senha(senha)
        with self.unidade_trabalho() as repositorio:
            if repositorio.obter("usuarios", email=email):
                raise ErroNegocio("EMAIL_INDISPONIVEL", "Nao foi possivel cadastrar este email.")
            usuario = repositorio.adicionar(
                "usuarios",
                nome=nome,
                email=email,
                senha_hash=codificada,
                perfil=Perfil.CLIENTE,
                consentimento=int(consentimento),
                criado_em=agora(),
            )
            repositorio.adicionar(
                "consentimentos",
                usuario_id=usuario["id"],
                concedido=int(consentimento),
                finalidade="FIDELIDADE",
                versao_politica="1.0",
                criado_em=agora(),
            )
            auditar(
                repositorio, Ator(usuario["id"], Perfil.CLIENTE, None), "CADASTRO", usuario["id"]
            )
            return {"id": usuario["id"], "nome": nome, "email": email, "perfil": Perfil.CLIENTE}

    def entrar(self, email, senha):
        with self.unidade_trabalho() as repositorio:
            usuario = repositorio.obter("usuarios", email=email, ativo=1)
        codificada = (
            usuario["senha_hash"]
            if usuario
            else self.seguranca.gerar_hash_senha("senha-ficticia-autenticacao")
        )
        valido = self.seguranca.verificar_senha(senha, codificada)
        if not usuario or not valido:
            raise ErroNegocio("CREDENCIAIS_INVALIDAS", "Email ou senha invalidos.", 401)
        with self.unidade_trabalho() as repositorio:
            auditar(
                repositorio,
                Ator(usuario["id"], Perfil(usuario["perfil"]), usuario["unidade_id"]),
                "AUTENTICACAO",
                usuario["id"],
            )
        return {"tokenAcesso": self.seguranca.emitir_token(usuario["id"]), "tipoToken": "bearer"}

    def autenticar(self, token):
        usuario_id = self.seguranca.ler_token(token)
        with self.unidade_trabalho() as repositorio:
            usuario = repositorio.obter("usuarios", id=usuario_id, ativo=1)
            if not usuario:
                raise ErroNegocio("NAO_AUTENTICADO", "Usuario inativo ou inexistente.", 401)
            return Ator(usuario_id, Perfil(usuario["perfil"]), usuario["unidade_id"])

    def consultar_perfil(self, ator):
        with self.unidade_trabalho() as repositorio:
            usuario = exigir_registro(repositorio, "usuarios", id=ator.id)
            auditar(repositorio, ator, "CONSULTA_DADOS_PESSOAIS", ator.id)
            return {
                "id": usuario["id"],
                "nome": usuario["nome"],
                "email": usuario["email"],
                "perfil": usuario["perfil"],
                "consentimentoFidelidade": bool(usuario["consentimento"]),
            }

    def consentimento(self, ator, concedido):
        with self.unidade_trabalho() as repositorio:
            repositorio.atualizar("usuarios", ator.id, consentimento=int(concedido))
            repositorio.adicionar(
                "consentimentos",
                usuario_id=ator.id,
                concedido=int(concedido),
                finalidade="FIDELIDADE",
                versao_politica="1.0",
                criado_em=agora(),
            )
            auditar(repositorio, ator, "CONSENTIMENTO_ATUALIZADO", ator.id)
        return {"consentimentoFidelidade": concedido, "versaoPolitica": "1.0"}

    def anonimizar(self, ator):
        with self.unidade_trabalho() as repositorio:
            for status in [
                StatusPedido.AGUARDANDO_PAGAMENTO,
                StatusPedido.EM_PREPARO,
                StatusPedido.PRONTO,
            ]:
                if repositorio.obter("pedidos", usuario_id=ator.id, status=status):
                    raise ErroNegocio(
                        "PEDIDO_EM_ABERTO", "Conclua ou cancele seus pedidos antes de anonimizar."
                    )
            repositorio.atualizar(
                "usuarios",
                ator.id,
                nome="Anonimizado",
                email=f"{ator.id}@anon.invalid",
                senha_hash="revogada",
                ativo=0,
                consentimento=0,
                pontos=0,
            )
            repositorio.adicionar(
                "consentimentos",
                usuario_id=ator.id,
                concedido=0,
                finalidade="FIDELIDADE",
                versao_politica="1.0",
                criado_em=agora(),
            )
            auditar(repositorio, ator, "ANONIMIZACAO", ator.id)


class Catalogo:
    def __init__(self, unidade_trabalho: UnidadeTrabalho):
        self.unidade_trabalho = unidade_trabalho

    def listar_unidades(self, pagina, limite):
        with self.unidade_trabalho() as repositorio:
            return paginar(repositorio, "unidades", pagina, limite, ativo=1)

    def cadastrar_unidade(self, ator, nome, regiao):
        ator.exigir(Perfil.ADMIN)
        with self.unidade_trabalho() as repositorio:
            unidade = repositorio.adicionar("unidades", nome=nome, regiao=regiao)
            auditar(repositorio, ator, "UNIDADE_CRIADA", unidade["id"])
            return unidade

    def cadastrar_produto(self, ator, nome, preco_centavos):
        ator.exigir(Perfil.ADMIN)
        with self.unidade_trabalho() as repositorio:
            produto = repositorio.adicionar("produtos", nome=nome, preco_centavos=preco_centavos)
            auditar(repositorio, ator, "PRODUTO_CRIADO", produto["id"])
            return produto

    def listar_produtos(self, pagina, limite):
        with self.unidade_trabalho() as repositorio:
            return paginar(repositorio, "produtos", pagina, limite, ativo=1)

    def cardapio(self, unidade_id, pagina, limite):
        with self.unidade_trabalho() as repositorio:
            exigir_registro(repositorio, "unidades", id=unidade_id, ativo=1)
            resultado = paginar(
                repositorio, "estoques", pagina, limite, unidade_id=unidade_id, disponivel=1
            )
            resultado["itens"] = [
                {
                    **entrada,
                    "produto": exigir_registro(repositorio, "produtos", id=entrada["produto_id"]),
                }
                for entrada in resultado["itens"]
            ]
            return resultado

    def movimentar_estoque(self, ator, unidade_id, produto_id, variacao, motivo):
        ator.exigir(Perfil.ADMIN, Perfil.GERENTE)
        ator.verificar_unidade(unidade_id)
        with self.unidade_trabalho() as repositorio:
            exigir_registro(repositorio, "unidades", id=unidade_id, ativo=1)
            exigir_registro(repositorio, "produtos", id=produto_id, ativo=1)
            if not repositorio.obter("estoques", unidade_id=unidade_id, produto_id=produto_id):
                repositorio.adicionar("estoques", unidade_id=unidade_id, produto_id=produto_id)
            repositorio.ajustar_estoque(unidade_id, produto_id, variacao)
            repositorio.adicionar(
                "movimentacoes_estoque",
                unidade_id=unidade_id,
                produto_id=produto_id,
                variacao=variacao,
                motivo=motivo,
                ator_id=ator.id,
                criado_em=agora(),
            )
            auditar(repositorio, ator, "ESTOQUE_MOVIMENTADO", produto_id)
            return exigir_registro(
                repositorio, "estoques", unidade_id=unidade_id, produto_id=produto_id
            )

    def consultar_estoque(self, ator, unidade_id, pagina, limite):
        ator.exigir(Perfil.ADMIN, Perfil.GERENTE)
        ator.verificar_unidade(unidade_id)
        with self.unidade_trabalho() as repositorio:
            exigir_registro(repositorio, "unidades", id=unidade_id)
            return paginar(repositorio, "estoques", pagina, limite, unidade_id=unidade_id)


class GestaoPedidos:
    def __init__(self, unidade_trabalho: UnidadeTrabalho, servico_pagamento: ServicoPagamento):
        self.unidade_trabalho = unidade_trabalho
        self.servico_pagamento = servico_pagamento

    def exigir_acesso(self, repositorio, ator, pedido_id):
        pedido = exigir_registro(repositorio, "pedidos", id=pedido_id)
        if ator.perfil == Perfil.CLIENTE:
            if pedido["usuario_id"] != ator.id:
                raise ErroNegocio("SEM_PERMISSAO", "Pedido de outro cliente.", 403)
        else:
            ator.verificar_unidade(pedido["unidade_id"])
        return pedido

    def serializar(self, repositorio, pedido):
        return {
            "id": pedido["id"],
            "clienteId": pedido["usuario_id"],
            "unidadeId": pedido["unidade_id"],
            "canalPedido": pedido["canal"],
            "status": pedido["status"],
            "totalCentavos": pedido["total_centavos"],
            "descontoCentavos": pedido["desconto_centavos"],
            "pontosResgatados": pedido["pontos_resgatados"],
            "criadoEm": pedido["criado_em"],
            "itens": repositorio.listar("itens_pedido", pedido_id=pedido["id"]),
        }

    def criar(self, ator, unidade_id, canal, itens, chave, pontos=0):
        ator.exigir(Perfil.CLIENTE, Perfil.ATENDENTE, Perfil.ADMIN)
        if ator.perfil != Perfil.CLIENTE:
            ator.verificar_unidade(unidade_id)
        quantidades = Counter()
        for item in itens:
            quantidades[item["produtoId"]] += item["quantidade"]
        conteudo_canonico = {
            "unit": unidade_id,
            "canal": canal,
            "itens": sorted(quantidades.items()),
            "pontos": pontos,
        }
        resumo = hashlib.sha256(json.dumps(conteudo_canonico, sort_keys=True).encode()).hexdigest()
        with self.unidade_trabalho() as repositorio:
            existente = repositorio.obter("pedidos", usuario_id=ator.id, chave_idempotencia=chave)
            if existente:
                if existente["resumo_requisicao"] != resumo:
                    raise ErroNegocio(
                        "IDEMPOTENCIA_CONFLITANTE", "Chave ja utilizada com outro conteudo."
                    )
                return self.serializar(repositorio, existente)
            exigir_registro(repositorio, "unidades", id=unidade_id, ativo=1)
            precos = {}
            for produto_id, quantidade in quantidades.items():
                produto = exigir_registro(repositorio, "produtos", id=produto_id, ativo=1)
                entrada = repositorio.obter(
                    "estoques", unidade_id=unidade_id, produto_id=produto_id, disponivel=1
                )
                if not entrada or entrada["quantidade"] < quantidade:
                    raise ErroNegocio(
                        "ESTOQUE_INSUFICIENTE",
                        "Produto indisponivel ou estoque insuficiente na unidade.",
                    )
                precos[produto_id] = produto["preco_centavos"]
            subtotal = sum(
                (precos[produto_id] * quantidade for produto_id, quantidade in quantidades.items())
            )
            usuario = exigir_registro(repositorio, "usuarios", id=ator.id)
            if pontos:
                if not usuario["consentimento"]:
                    raise ErroNegocio(
                        "CONSENTIMENTO_NECESSARIO",
                        "Autorize a participacao no programa de fidelidade.",
                    )
                if pontos > subtotal // 2:
                    raise ErroNegocio(
                        "RESGATE_EXCEDIDO", "Desconto de fidelidade limitado a 50% do pedido."
                    )
                repositorio.ajustar_pontos(ator.id, -pontos)
            pedido = repositorio.adicionar(
                "pedidos",
                usuario_id=ator.id,
                unidade_id=unidade_id,
                canal=canal,
                status=StatusPedido.AGUARDANDO_PAGAMENTO,
                total_centavos=subtotal - pontos,
                desconto_centavos=pontos,
                pontos_resgatados=pontos,
                chave_idempotencia=chave,
                resumo_requisicao=resumo,
                criado_em=agora(),
            )
            for produto_id, quantidade in quantidades.items():
                repositorio.ajustar_estoque(unidade_id, produto_id, -quantidade)
                repositorio.adicionar(
                    "itens_pedido",
                    pedido_id=pedido["id"],
                    produto_id=produto_id,
                    quantidade=quantidade,
                    preco_unitario_centavos=precos[produto_id],
                )
                repositorio.adicionar(
                    "movimentacoes_estoque",
                    unidade_id=unidade_id,
                    produto_id=produto_id,
                    variacao=-quantidade,
                    motivo=f"PEDIDO:{pedido['id']}",
                    ator_id=ator.id,
                    criado_em=agora(),
                )
            if pontos:
                repositorio.adicionar(
                    "eventos_fidelidade",
                    usuario_id=ator.id,
                    pedido_id=pedido["id"],
                    variacao=-pontos,
                    tipo="RESGATE",
                    criado_em=agora(),
                )
            auditar(repositorio, ator, "PEDIDO_CRIADO", pedido["id"])
            return self.serializar(repositorio, pedido)

    def obter(self, ator, pedido_id):
        with self.unidade_trabalho() as repositorio:
            pedido = self.exigir_acesso(repositorio, ator, pedido_id)
            return self.serializar(repositorio, pedido)

    def listar(self, ator, pagina, limite, canal=None, status=None):
        filtros = {}
        if ator.perfil == Perfil.CLIENTE:
            filtros["usuario_id"] = ator.id
        elif ator.perfil != Perfil.ADMIN:
            filtros["unidade_id"] = ator.unidade_id
        if canal:
            filtros["canal"] = canal
        if status:
            filtros["status"] = status
        with self.unidade_trabalho() as repositorio:
            resultado = paginar(repositorio, "pedidos", pagina, limite, **filtros)
            resultado["itens"] = [
                self.serializar(repositorio, pedido) for pedido in resultado["itens"]
            ]
            return resultado

    def devolver_saldos(self, repositorio, ator, pedido):
        for item in repositorio.listar("itens_pedido", pedido_id=pedido["id"]):
            repositorio.ajustar_estoque(
                pedido["unidade_id"], item["produto_id"], item["quantidade"]
            )
            repositorio.adicionar(
                "movimentacoes_estoque",
                unidade_id=pedido["unidade_id"],
                produto_id=item["produto_id"],
                variacao=item["quantidade"],
                motivo=f"CANCELAMENTO:{pedido['id']}",
                ator_id=ator.id,
                criado_em=agora(),
            )
        if pedido["pontos_resgatados"]:
            repositorio.ajustar_pontos(pedido["usuario_id"], pedido["pontos_resgatados"])
            repositorio.adicionar(
                "eventos_fidelidade",
                usuario_id=pedido["usuario_id"],
                pedido_id=pedido["id"],
                variacao=pedido["pontos_resgatados"],
                tipo="ESTORNO",
                criado_em=agora(),
            )

    def pagar(self, ator, pedido_id, resultado):
        ator.exigir(Perfil.CLIENTE, Perfil.ATENDENTE, Perfil.ADMIN)
        with self.unidade_trabalho() as repositorio:
            pedido = self.exigir_acesso(repositorio, ator, pedido_id)
            pagamento = repositorio.obter("pagamentos", pedido_id=pedido_id)
            if pagamento:
                if pagamento["status"] != resultado:
                    raise ErroNegocio(
                        "PAGAMENTO_FINALIZADO", "Pagamento ja finalizado com outro resultado."
                    )
                return {
                    "pagamento": {**pagamento, "retorno": json.loads(pagamento["retorno"])},
                    "pedido": self.serializar(repositorio, pedido),
                }
            if pedido["status"] != StatusPedido.AGUARDANDO_PAGAMENTO:
                raise ErroNegocio("STATUS_INVALIDO", "Pedido nao aguarda pagamento.")
            retorno = self.servico_pagamento.solicitar(
                pedido_id, pedido["total_centavos"], resultado
            )
            pagamento = repositorio.adicionar(
                "pagamentos",
                pedido_id=pedido_id,
                status=resultado,
                valor_centavos=pedido["total_centavos"],
                retorno=json.dumps(retorno),
                criado_em=agora(),
            )
            status = StatusPedido.EM_PREPARO if resultado == "APROVADO" else StatusPedido.CANCELADO
            if resultado == "RECUSADO":
                self.devolver_saldos(repositorio, ator, pedido)
            repositorio.atualizar("pedidos", pedido_id, status=status)
            pedido["status"] = status
            auditar(repositorio, ator, f"PAGAMENTO_{resultado}", pedido_id)
            return {
                "pagamento": {**pagamento, "retorno": retorno},
                "pedido": self.serializar(repositorio, pedido),
            }

    def alterar_status(self, ator, pedido_id, destino):
        with self.unidade_trabalho() as repositorio:
            pedido = self.exigir_acesso(repositorio, ator, pedido_id)
            if destino == StatusPedido.CANCELADO:
                ator.exigir(Perfil.CLIENTE, Perfil.ATENDENTE, Perfil.GERENTE, Perfil.ADMIN)
                if (
                    ator.perfil == Perfil.CLIENTE
                    and pedido["status"] != StatusPedido.AGUARDANDO_PAGAMENTO
                ):
                    raise ErroNegocio(
                        "SEM_PERMISSAO", "Cliente pode cancelar apenas antes do pagamento.", 403
                    )
            elif destino == StatusPedido.PRONTO:
                ator.exigir(Perfil.COZINHA, Perfil.GERENTE, Perfil.ADMIN)
            elif destino == StatusPedido.ENTREGUE:
                ator.exigir(Perfil.ATENDENTE, Perfil.GERENTE, Perfil.ADMIN)
            else:
                raise ErroNegocio("STATUS_INVALIDO", "Status controlado pelo fluxo de pagamento.")
            pedido_dominio = Pedido(StatusPedido(pedido["status"]), pedido["total_centavos"])
            pedido_dominio.alterar_status(destino)
            if destino == StatusPedido.CANCELADO:
                self.devolver_saldos(repositorio, ator, pedido)
                pagamento = repositorio.obter("pagamentos", pedido_id=pedido_id)
                if pagamento and pagamento["status"] == "APROVADO":
                    retorno = json.loads(pagamento["retorno"])
                    retorno["status"] = "ESTORNADO"
                    retorno["mensagem"] = "Estorno simulado registrado."
                    repositorio.atualizar(
                        "pagamentos",
                        pagamento["id"],
                        status="ESTORNADO",
                        retorno=json.dumps(retorno),
                    )
            if destino == StatusPedido.ENTREGUE:
                usuario = exigir_registro(repositorio, "usuarios", id=pedido["usuario_id"])
                if usuario["consentimento"] and pedido_dominio.pontos_fidelidade:
                    repositorio.ajustar_pontos(usuario["id"], pedido_dominio.pontos_fidelidade)
                    repositorio.adicionar(
                        "eventos_fidelidade",
                        usuario_id=usuario["id"],
                        pedido_id=pedido_id,
                        variacao=pedido_dominio.pontos_fidelidade,
                        tipo="CREDITO",
                        criado_em=agora(),
                    )
            repositorio.atualizar("pedidos", pedido_id, status=destino)
            auditar(repositorio, ator, f"PEDIDO_{destino}", pedido_id)
            pedido["status"] = destino
            return self.serializar(repositorio, pedido)

    def consultar_fidelidade(self, ator, pagina, limite):
        with self.unidade_trabalho() as repositorio:
            usuario = exigir_registro(repositorio, "usuarios", id=ator.id)
            auditar(repositorio, ator, "CONSULTA_FIDELIDADE", ator.id)
            return {
                "saldo": usuario["pontos"],
                "consentimento": bool(usuario["consentimento"]),
                "historico": paginar(
                    repositorio, "eventos_fidelidade", pagina, limite, usuario_id=ator.id
                ),
            }

    def consultar_auditorias(self, ator, pagina, limite):
        ator.exigir(Perfil.ADMIN)
        with self.unidade_trabalho() as repositorio:
            auditar(repositorio, ator, "CONSULTA_AUDITORIA", ator.id)
            return paginar(repositorio, "registros_auditoria", pagina, limite)
