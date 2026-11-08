# Arquitetura e regras de negócio

## Organização

| Camada | Responsabilidade |
| --- | --- |
| `domain` | Perfis, canais, estados do pedido e transições permitidas |
| `application` | Casos de uso de conta, catálogo, estoque, pedido, pagamento e fidelidade |
| `infrastructure` | SQLite, migrações, repositório, senha, JWT e pagamento simulado |
| `api` | Rotas HTTP, validação de entrada e respostas |

`montagem.py` reúne as dependências. As regras de negócio não executam SQL diretamente; o acesso aos dados ocorre por meio das portas da aplicação.

## Pedido

Para criar um pedido, o usuário deve estar autenticado. A unidade e os produtos precisam estar ativos e ter estoque suficiente.

1. A API valida canal, itens e `Idempotency-Key`.
2. A aplicação consulta os preços e agrupa itens repetidos.
3. A mesma transação grava pedido, itens, movimentações, auditoria e reserva o estoque.
4. O pagamento simulado atualiza o pedido para `EM_PREPARO`, ou o cancela e devolve o estoque.
5. COZINHA marca o pedido como pronto e ATENDENTE registra a entrega.

O total é calculado no servidor em centavos. Repetir a mesma chave de idempotência com o mesmo conteúdo devolve o pedido existente. Usar a chave com outro conteúdo retorna conflito.

## Fidelidade e privacidade

O cliente pode conceder ou revogar o consentimento de fidelidade. Pontos são creditados apenas após a entrega e podem ser usados como desconto, respeitando o saldo e o limite de 50% do pedido.

`DELETE /usuarios/eu` anonimiza os dados da conta. A operação não é permitida quando há pedido aberto.

## Estados do pedido

| Estado atual | Próximo estado | Condição |
| --- | --- | --- |
| `AGUARDANDO_PAGAMENTO` | `EM_PREPARO` | Pagamento aprovado |
| `AGUARDANDO_PAGAMENTO` | `CANCELADO` | Pagamento recusado ou cancelamento autorizado |
| `EM_PREPARO` | `PRONTO` | Cozinha, gerente ou administrador |
| `EM_PREPARO` | `CANCELADO` | Atendente, gerente ou administrador |
| `PRONTO` | `ENTREGUE` | Atendente, gerente ou administrador |

Clientes só cancelam antes do pagamento. Funcionários atuam na unidade vinculada à conta; ADMIN pode operar em qualquer unidade.

## Persistência

O banco possui tabelas para usuários, unidades, produtos, estoques, pedidos, itens, pagamentos, fidelidade, consentimentos e auditoria. As migrações são registradas em `migracoes_esquema`.

O SQLite usa chaves estrangeiras, restrições de saldo e transações. O modo WAL é usado para o ambiente local. Os testes cobrem a disputa por estoque em pedidos concorrentes.

## Limites atuais

O pagamento é simulado e não recebe dados de cartão. Não há campanhas promocionais, relatórios financeiros, expiração automática de reservas ou testes de carga.
