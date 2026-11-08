# Arquitetura e regras de negócio

## Organização

O projeto separa as regras do pedido dos detalhes de HTTP e banco de dados:

| Camada | Responsabilidade |
| --- | --- |
| `domain` | Perfis, canais, estados do pedido e transições permitidas |
| `application` | Criação de pedidos, pagamento, estoque, fidelidade e controle de acesso |
| `infrastructure` | SQLite, migrations, repositório, hash de senha, JWT e pagamento mock |
| `api` | Rotas, validação de entrada, respostas e documentação OpenAPI |

`montagem.py` conecta os serviços às implementações das portas. A aplicação não contém SQL; recebe um gerenciador de transações e os serviços de segurança e pagamento. Cada operação confirma ou desfaz suas alterações em conjunto.

## Fluxo de pedido e pagamento

Para criar um pedido, o usuário precisa estar autenticado. A unidade e os produtos devem estar ativos, com estoque suficiente. O contrato exige `canalPedido`, itens com quantidades positivas e o cabeçalho `Idempotency-Key`.

1. A API valida a entrada. A aplicação agrupa produtos repetidos e verifica a chave de idempotência.
2. Os preços são lidos do banco. O cliente não informa o total.
3. A transação registra pedido e itens, reserva o estoque, desconta os pontos resgatados e grava a auditoria. Uma falha desfaz a operação inteira.
4. `POST /pagamentos` solicita o pagamento mock e registra o resultado e o retorno do serviço.
5. `APROVADO` coloca o pedido em preparo. `RECUSADO` cancela e devolve estoque e pontos. `TEMPO_ESGOTADO` retorna 503 e mantém o pedido aguardando pagamento, permitindo tentar novamente.
6. A cozinha marca o pedido como pronto. O atendente registra a entrega. Os pontos são creditados nessa última etapa, se houver consentimento.

Ao terminar, o pedido mantém o canal de origem, os preços da compra e o resultado do pagamento. Repetir a mesma chave com os mesmos dados devolve o pedido existente; mudar o conteúdo com a mesma chave retorna 409. Um pagamento já concluído não pode receber outro resultado.

O pedido pertence ao usuário autenticado. No balcão, quando o atendente cria o pedido, ele fica vinculado ao operador. Associar esse pedido a um consumidor identificado ainda não foi implementado.

## Valores e fidelidade

Todos os valores são inteiros em centavos. Cada real pago gera um ponto na entrega, desconsiderando os centavos restantes. Cada ponto resgatado desconta um centavo, até o limite de 50% do subtotal.

O resgate exige consentimento e saldo suficiente. Os pontos são descontados na criação e devolvidos em caso de cancelamento. A revogação do consentimento impede novos créditos e resgates, mantendo o histórico das operações anteriores.

Campanhas sazonais e segmentadas ficam para uma próxima versão. A regra proposta é definir período de vigência em UTC, unidades participantes e condições de acúmulo com o desconto de fidelidade.

## Estados e cancelamento

| Estado atual | Próximo estado | Condição |
| --- | --- | --- |
| `AGUARDANDO_PAGAMENTO` | `EM_PREPARO` | Pagamento aprovado |
| `AGUARDANDO_PAGAMENTO` | `CANCELADO` | Pagamento recusado ou cancelamento autorizado |
| `EM_PREPARO` | `PRONTO` | Cozinha, gerente ou administrador |
| `EM_PREPARO` | `CANCELADO` | Atendente, gerente ou administrador |
| `PRONTO` | `ENTREGUE` | Atendente, gerente ou administrador |

`ENTREGUE` e `CANCELADO` encerram o fluxo. O cliente só cancela antes do pagamento. Se um operador cancelar um pedido em preparo já pago, o mock registra o pagamento como `ESTORNADO`. Nenhum pagamento ou estorno real é executado.

Funcionários atuam apenas na unidade vinculada à conta. O administrador pode operar em toda a rede.

## Persistência

O DER corresponde às tabelas `usuarios`, `unidades`, `produtos`, `estoques`, `pedidos`, `itens_pedido`, `pagamentos`, `movimentacoes_estoque`, `eventos_fidelidade`, `consentimentos` e `registros_auditoria`. A tabela `migracoes_esquema` controla as versões aplicadas.

As restrições do banco impedem saldo negativo, duplicação de estoque por unidade/produto, reutilização da chave de pedido pelo mesmo usuário e mais de um pagamento por pedido. Eventos de fidelidade são únicos por pedido e tipo.

## Limites desta versão

SQLite simplifica a execução local. O modo WAL e as transações de escrita serializadas protegem os saldos; o teste concorrente verifica a disputa pelo mesmo estoque. Ainda não há validação de carga nem infraestrutura de alta disponibilidade.

O gateway mock é local e determinístico, por isso é chamado dentro da transação. Uma integração remota precisaria tratar envio, confirmação e reconciliação fora dessa transação, por exemplo com outbox e callbacks autenticados. Para expansão da rede, também será necessário avaliar PostgreSQL, bloqueios por saldo, monitoramento e recuperação de falhas.

Reservas de estoque não expiram automaticamente. Nesta versão, o cancelamento libera o saldo.
