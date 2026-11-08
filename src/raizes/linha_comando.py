import argparse
import os

from raizes.configuracao import Configuracoes
from raizes.infrastructure.banco_dados import BancoDados
from raizes.infrastructure.dados_iniciais import popular
from raizes.infrastructure.seguranca import SegurancaJwt


def principal():
    interpretador = argparse.ArgumentParser(prog="raizes")
    interpretador.add_argument("comando", choices=["migrar", "popular"])
    argumentos = interpretador.parse_args()
    configuracoes = Configuracoes.do_ambiente()
    banco = BancoDados(configuracoes.banco)
    if argumentos.comando == "migrar":
        banco.migrar()
        print("MigraÃ§Ãµes aplicadas.")
    else:
        popular(
            banco,
            SegurancaJwt(configuracoes.segredo_jwt, configuracoes.duracao_token_minutos),
            os.environ.get("RAIZES_SENHA_INICIAL", ""),
        )
        print("Dados iniciais cadastrados sem sobrescrever registros existentes.")


if __name__ == "__main__":
    principal()
