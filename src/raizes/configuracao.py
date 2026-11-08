import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Configuracoes:
    banco: str
    segredo_jwt: str
    duracao_token_minutos: int

    @classmethod
    def do_ambiente(cls):
        load_dotenv()
        segredo = os.environ.get("RAIZES_SEGREDO_JWT", "")
        if len(segredo) < 32:
            raise ValueError("Defina RAIZES_SEGREDO_JWT com pelo menos 32 caracteres.")
        minutos = int(os.environ.get("RAIZES_DURACAO_TOKEN_MINUTOS", "30"))
        if not 1 <= minutos <= 1440:
            raise ValueError("RAIZES_DURACAO_TOKEN_MINUTOS deve estar entre 1 e 1440.")
        return cls(os.environ.get("RAIZES_BANCO_DADOS", "dados/raizes.db"), segredo, minutos)
