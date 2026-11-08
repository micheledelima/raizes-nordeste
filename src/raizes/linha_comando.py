import argparse

from raizes.configuracao import Configuracoes
from raizes.infrastructure.banco_dados import BancoDados


def principal():
    interpretador = argparse.ArgumentParser(prog="raizes")
    interpretador.add_argument("comando", choices=["migrar"])
    interpretador.parse_args()
    configuracoes = Configuracoes.do_ambiente()
    BancoDados(configuracoes.banco).migrar()
    print("Migrações aplicadas.")


if __name__ == "__main__":
    principal()
