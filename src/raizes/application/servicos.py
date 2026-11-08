from datetime import UTC, datetime

from raizes.application.portas import Seguranca, UnidadeTrabalho, exigir_registro
from raizes.domain.modelos import Ator, ErroNegocio, Perfil


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
