class ErroNegocio(Exception):
    def __init__(self, codigo: str, mensagem: str, status: int = 409):
        self.codigo = codigo
        self.mensagem = mensagem
        self.status = status
        super().__init__(mensagem)
