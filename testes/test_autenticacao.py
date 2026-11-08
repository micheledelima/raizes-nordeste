from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from raizes.domain.modelos import Ator, ErroNegocio, Perfil
from raizes.infrastructure.banco_dados import BancoDados
from raizes.infrastructure.seguranca import SegurancaJwt
from raizes.montagem import montar_api

SEGREDO = "segredo-autenticacao-testes-com-32-caracteres"
SENHA = "Senha-de-teste-123!"


@pytest.fixture
def acesso(tmp_path, monkeypatch):
    caminho = str(tmp_path / "autenticacao.db")
    monkeypatch.setenv("RAIZES_BANCO_DADOS", caminho)
    monkeypatch.setenv("RAIZES_SEGREDO_JWT", SEGREDO)
    monkeypatch.setenv("RAIZES_DURACAO_TOKEN_MINUTOS", "30")
    banco = BancoDados(caminho)
    banco.migrar()
    with TestClient(montar_api()) as cliente:
        yield cliente, banco


def cadastrar(cliente, email="maria@example.com"):
    return cliente.post("/usuarios", json={"nome": "Maria Silva", "email": email, "senha": SENHA})


def entrar(cliente):
    return cliente.post("/autenticacao/entrar", json={"email": "maria@example.com", "senha": SENHA})


def test_cadastro_persiste_cliente_com_senha_protegida(acesso):
    cliente, banco = acesso
    resposta = cadastrar(cliente)
    assert resposta.status_code == 201
    assert resposta.json()["perfil"] == "CLIENTE"
    assert "senha" not in resposta.json() and "senha_hash" not in resposta.json()
    with banco.transacao() as repositorio:
        usuario = repositorio.obter("usuarios", email="maria@example.com")
        assert usuario["senha_hash"] != SENHA
        assert SegurancaJwt(SEGREDO).verificar_senha(SENHA, usuario["senha_hash"])
        assert repositorio.obter("registros_auditoria", acao="CADASTRO", recurso_id=usuario["id"])


def test_email_normalizado_nao_permite_cadastro_duplicado(acesso):
    cliente, _ = acesso
    assert cadastrar(cliente, "Maria@Example.com").status_code == 201
    assert cadastrar(cliente).status_code == 409


@pytest.mark.parametrize(
    "campo,valor", [("email", "invalido"), ("senha", "curta"), ("nome", "M"), ("perfil", "ADMIN")]
)
def test_cadastro_rejeita_dados_invalidos_e_elevacao_de_perfil(acesso, campo, valor):
    cliente, _ = acesso
    dados = {"nome": "Maria Silva", "email": "maria@example.com", "senha": SENHA, campo: valor}
    resposta = cliente.post("/usuarios", json=dados)
    assert resposta.status_code == 422
    assert resposta.json()["erro"]["codigo"] == "VALIDACAO"


def test_login_emite_token_e_permite_consulta_propria(acesso):
    cliente, _ = acesso
    cadastro = cadastrar(cliente).json()
    resposta = entrar(cliente)
    assert resposta.status_code == 200
    assert set(resposta.json()) == {"tokenAcesso", "tipoToken"}
    token = resposta.json()["tokenAcesso"]
    assert SegurancaJwt(SEGREDO).ler_token(token) == cadastro["id"]
    perfil = cliente.get("/usuarios/eu", headers={"Authorization": "Bearer " + token})
    assert perfil.status_code == 200
    assert perfil.json()["id"] == cadastro["id"]
    assert "senha_hash" not in perfil.json()


@pytest.mark.parametrize("email", ["maria@example.com", "inexistente@example.com"])
def test_login_rejeita_senha_errada_ou_usuario_inexistente(acesso, email):
    cliente, _ = acesso
    cadastrar(cliente)
    resposta = cliente.post(
        "/autenticacao/entrar", json={"email": email, "senha": "senha-incorreta"}
    )
    assert resposta.status_code == 401
    assert resposta.json()["erro"]["codigo"] == "CREDENCIAIS_INVALIDAS"


def test_consulta_sem_token_retorna_erro_padronizado(acesso):
    cliente, _ = acesso
    resposta = cliente.get("/usuarios/eu")
    assert resposta.status_code == 401
    assert set(resposta.json()["erro"]) == {"codigo", "mensagem", "requisicaoId"}
    assert resposta.json()["erro"]["requisicaoId"] == resposta.headers["X-Request-ID"]
    assert resposta.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize("tipo", ["expirado", "assinatura_invalida", "destinatario_invalido"])
def test_rejeita_tokens_invalidos(acesso, tipo):
    cliente, _ = acesso
    usuario = cadastrar(cliente).json()
    agora = datetime.now(UTC)
    declaracoes = {
        "sub": usuario["id"],
        "iat": agora - timedelta(minutes=2),
        "exp": agora + timedelta(minutes=1),
        "iss": "raizes-nordeste",
        "aud": "raizes-api",
    }
    chave = SEGREDO
    if tipo == "expirado":
        declaracoes["exp"] = agora - timedelta(minutes=1)
    elif tipo == "assinatura_invalida":
        chave = "outra-chave-de-assinatura-com-32-caracteres"
    else:
        declaracoes["aud"] = "outro-servico"
    token = jwt.encode(declaracoes, chave, algorithm="HS256")
    assert (
        cliente.get("/usuarios/eu", headers={"Authorization": "Bearer " + token}).status_code == 401
    )


def test_usuario_desativado_perde_acesso_com_token_valido(acesso):
    cliente, banco = acesso
    usuario = cadastrar(cliente).json()
    token = entrar(cliente).json()["tokenAcesso"]
    with banco.transacao() as repositorio:
        repositorio.atualizar("usuarios", usuario["id"], ativo=0)
    assert (
        cliente.get("/usuarios/eu", headers={"Authorization": "Bearer " + token}).status_code == 401
    )


def test_perfil_sem_permissao_e_rejeitado():
    ator = Ator("cliente", Perfil.CLIENTE, None)
    with pytest.raises(ErroNegocio) as falha:
        ator.exigir(Perfil.ADMIN)
    assert falha.value.status == 403


def test_hash_usa_sal_aleatorio_e_valida_senha():
    seguranca = SegurancaJwt(SEGREDO)
    primeiro = seguranca.gerar_hash_senha(SENHA)
    segundo = seguranca.gerar_hash_senha(SENHA)
    assert primeiro != segundo
    assert seguranca.verificar_senha(SENHA, primeiro)
    assert not seguranca.verificar_senha("incorreta", primeiro)


def test_rejeita_segredo_jwt_curto():
    with pytest.raises(ValueError):
        SegurancaJwt("segredo")
