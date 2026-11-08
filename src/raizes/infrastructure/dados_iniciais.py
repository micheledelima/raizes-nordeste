from raizes.application.servicos import agora
from raizes.domain.modelos import Perfil

UNIDADE_RECIFE = "10000000-0000-4000-8000-000000000001"
UNIDADE_NATAL = "10000000-0000-4000-8000-000000000002"
PRODUTO_TAPIOCA = "20000000-0000-4000-8000-000000000001"
PRODUTO_CUSCUZ = "20000000-0000-4000-8000-000000000002"


def popular(banco, seguranca, senha):
    if len(senha) < 12 or senha.startswith("substitua"):
        raise ValueError("Defina RAIZES_SENHA_INICIAL com pelo menos 12 caracteres.")
    codificada = seguranca.gerar_hash_senha(senha)
    with banco.transacao() as repositorio:
        for unidade_id, nome, regiao in [
            (UNIDADE_RECIFE, "Recife Centro", "Pernambuco"),
            (UNIDADE_NATAL, "Natal Centro", "Rio Grande do Norte"),
        ]:
            if not repositorio.obter("unidades", id=unidade_id):
                repositorio.adicionar("unidades", id=unidade_id, nome=nome, regiao=regiao)
        for produto_id, nome, preco in [
            (PRODUTO_TAPIOCA, "Tapioca de queijo", 1200),
            (PRODUTO_CUSCUZ, "Cuscuz recheado", 1800),
        ]:
            if not repositorio.obter("produtos", id=produto_id):
                repositorio.adicionar("produtos", id=produto_id, nome=nome, preco_centavos=preco)
            for unidade_id in [UNIDADE_RECIFE, UNIDADE_NATAL]:
                if not repositorio.obter("estoques", unidade_id=unidade_id, produto_id=produto_id):
                    repositorio.adicionar(
                        "estoques", unidade_id=unidade_id, produto_id=produto_id, quantidade=100
                    )
        for indice, perfil in enumerate(Perfil, start=1):
            email = f"{perfil.lower()}@example.com"
            if not repositorio.obter("usuarios", email=email):
                usuario = repositorio.adicionar(
                    "usuarios",
                    id=f"30000000-0000-4000-8000-{indice:012d}",
                    nome=f"Demo {perfil}",
                    email=email,
                    senha_hash=codificada,
                    perfil=perfil,
                    unidade_id=None if perfil in [Perfil.CLIENTE, Perfil.ADMIN] else UNIDADE_RECIFE,
                    consentimento=int(perfil == Perfil.CLIENTE),
                    criado_em=agora(),
                )
                repositorio.adicionar(
                    "consentimentos",
                    usuario_id=usuario["id"],
                    concedido=usuario["consentimento"],
                    finalidade="FIDELIDADE",
                    versao_politica="1.0",
                    criado_em=agora(),
                )
