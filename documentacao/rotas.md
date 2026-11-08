# Rotas da API

O Swagger está em `/docs` e o contrato OpenAPI em `/openapi.json`. As rotas usam JSON. Valores monetários são inteiros em centavos; listagens aceitam `pagina` e `limite` de 1 a 100.

Erros seguem este formato:

```json
{
  "erro": {
    "codigo": "CODIGO_DO_ERRO",
    "mensagem": "Descrição do erro.",
    "requisicaoId": "uuid"
  }
}
```

## Acesso público

| Método | Rota | Finalidade |
| --- | --- | --- |
| GET | `/healthcheck` | Verificar se a API responde |
| POST | `/usuarios` | Cadastrar CLIENTE |
| POST | `/autenticacao/entrar` | Obter token Bearer |
| GET | `/unidades` | Listar unidades ativas |
| GET | `/produtos` | Listar produtos ativos |
| GET | `/unidades/{unidadeId}/cardapio` | Consultar produtos disponíveis na unidade |

Cadastro recebe `nome`, `email`, `senha` e `consentimentoFidelidade`. Login recebe `email` e `senha`, devolvendo `tokenAcesso` e `tipoToken`.

## Conta e fidelidade

| Método | Rota | Acesso |
| --- | --- | --- |
| GET | `/usuarios/eu` | Usuário autenticado |
| PUT | `/usuarios/eu/consentimentos` | Usuário autenticado |
| DELETE | `/usuarios/eu` | Usuário autenticado |
| GET | `/fidelidade` | Usuário autenticado |

O corpo de consentimento é `{ "concedido": true }`. A consulta de fidelidade devolve saldo, consentimento e histórico paginado.

## Administração de catálogo e estoque

| Método | Rota | Acesso |
| --- | --- | --- |
| POST | `/unidades` | ADMIN |
| POST | `/produtos` | ADMIN |
| GET | `/estoques/{unidadeId}` | GERENTE da unidade ou ADMIN |
| POST | `/estoques/movimentacoes` | GERENTE da unidade ou ADMIN |

Unidade recebe `nome` e `regiao`. Produto recebe `nome` e `precoCentavos`. Movimentação recebe `unidadeId`, `produtoId`, `quantidade` e `motivo`; quantidade não pode ser zero e o estoque não pode ficar negativo.

## Pedidos e pagamentos

| Método | Rota | Acesso |
| --- | --- | --- |
| POST | `/pedidos` | CLIENTE, ATENDENTE ou ADMIN |
| GET | `/pedidos` | Usuário autenticado |
| GET | `/pedidos/{pedidoId}` | Cliente proprietário, equipe da unidade ou ADMIN |
| PATCH | `/pedidos/{pedidoId}/status` | Conforme o status |
| POST | `/pagamentos` | Cliente proprietário, ATENDENTE da unidade ou ADMIN |

Criação de pedido exige o cabeçalho `Idempotency-Key` e este corpo:

```json
{
  "unidadeId": "uuid",
  "canalPedido": "TOTEM",
  "itens": [{"produtoId": "uuid", "quantidade": 2}],
  "pontosResgate": 0
}
```

Os canais são `APP`, `TOTEM`, `BALCAO`, `PICKUP` e `WEB`. A listagem permite filtrar por `canalPedido` e `status`.

O pagamento recebe `pedidoId` e `resultado`: `APROVADO`, `RECUSADO` ou `TEMPO_ESGOTADO`. O último caso retorna 503 e mantém o pedido aguardando nova tentativa.

Para mudança de status, envie `{ "status": "PRONTO" }`, `{ "status": "ENTREGUE" }` ou `{ "status": "CANCELADO" }`. COZINHA marca pronto; ATENDENTE registra a entrega; CLIENTE só cancela antes do pagamento.

## Auditoria

| Método | Rota | Acesso |
| --- | --- | --- |
| GET | `/auditorias` | ADMIN |

A rota devolve registros paginados de ações realizadas no sistema.
