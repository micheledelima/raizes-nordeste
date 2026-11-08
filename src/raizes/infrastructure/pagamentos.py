from raizes.domain.modelos import ErroNegocio


class PagamentoSimulado:
    def solicitar(self, pedido_id: str, valor_centavos: int, resultado: str) -> dict:
        if resultado == "TEMPO_ESGOTADO":
            raise ErroNegocio(
                "PAGAMENTO_INDISPONIVEL",
                "ServiÃ§o de pagamento simulado indisponÃ­vel; repita a solicitacao.",
                503,
            )
        return {
            "provedor": "SIMULADO",
            "referencia": f"simulado-{pedido_id}",
            "status": resultado,
            "valorCentavos": valor_centavos,
            "mensagem": "Pagamento simulado aprovado."
            if resultado == "APROVADO"
            else "Pagamento simulado recusado.",
        }
