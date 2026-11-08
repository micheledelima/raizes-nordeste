import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Configuracoes:
    banco: str

    @classmethod
    def do_ambiente(cls):
        load_dotenv()
        return cls(os.environ.get("RAIZES_BANCO_DADOS", "dados/raizes.db"))
