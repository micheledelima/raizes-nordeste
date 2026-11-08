import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

import jwt

from raizes.domain.modelos import ErroNegocio


class SegurancaJwt:
    def __init__(self, segredo: str, minutos: int = 30):
        if len(segredo) < 32 or segredo.startswith("substitua"):
            raise ValueError(
                "Configure RAIZES_SEGREDO_JWT com uma chave aleatoria de pelo menos 32 caracteres."
            )
        self.segredo = segredo
        self.minutos = minutos

    def gerar_hash_senha(self, senha: str) -> str:
        sal_criptografico = secrets.token_bytes(16)
        resumo = hashlib.scrypt(senha.encode(), salt=sal_criptografico, n=16384, r=8, p=1)
        return f"scrypt${sal_criptografico.hex()}${resumo.hex()}"

    def verificar_senha(self, senha: str, codificada: str) -> bool:
        try:
            _, sal_criptografico, esperado = codificada.split("$")
            obtido = hashlib.scrypt(
                senha.encode(), salt=bytes.fromhex(sal_criptografico), n=16384, r=8, p=1
            )
            return hmac.compare_digest(obtido.hex(), esperado)
        except (ValueError, TypeError):
            return False

    def emitir_token(self, usuario_id: str) -> str:
        agora = datetime.now(UTC)
        return jwt.encode(
            {
                "sub": usuario_id,
                "iat": agora,
                "exp": agora + timedelta(minutes=self.minutos),
                "iss": "raizes-nordeste",
                "aud": "raizes-api",
            },
            self.segredo,
            algorithm="HS256",
        )

    def ler_token(self, token: str) -> str:
        try:
            declaracoes = jwt.decode(
                token,
                self.segredo,
                algorithms=["HS256"],
                issuer="raizes-nordeste",
                audience="raizes-api",
                options={"require": ["sub", "exp", "iat"]},
            )
            return declaracoes["sub"]
        except jwt.InvalidTokenError as erro:
            raise ErroNegocio("NAO_AUTENTICADO", "Token invalido ou expirado.", 401) from erro
