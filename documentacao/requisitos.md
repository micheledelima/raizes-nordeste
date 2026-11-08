# Requisitos e escopo

A Raízes do Nordeste atende por aplicativo, totem, balcão, retirada e web. O sistema precisa reunir os pedidos desses canais sem misturar o estoque das lojas. Clientes consultam o cardápio e acompanham pedidos; a equipe da unidade prepara e entrega; a administração acompanha as operações da rede.

## Requisitos funcionais

| ID | Requisito | Atendimento nesta versão |
| --- | --- | --- |
| RF01 | Cadastro e autenticação com perfis | Cadastro público de CLIENTE, contas de equipe pelo seed, JWT e senha com hash scrypt |
| RF02 | Gestão de unidades e produtos | Cadastro por ADMIN e consulta paginada; edição, desativação e gestão de funcionários pendentes |
| RF03 | Consulta de cardápio por unidade | Produtos e disponibilidade do estoque local |
| RF04 | Criação e consulta de pedidos | Itens, preços da compra, canal obrigatório e filtros por canal e status |
| RF05 | Atualização de status | Pagamento inicia preparo; cozinha marca pronto; atendente registra entrega |
| RF06 | Cancelamento | Devolução de estoque e pontos; estorno mock quando aplicável; bloqueio após pronto |
| RF07 | Controle de estoque | Entradas, saídas e reserva transacional, com auditoria e saldo não negativo |
| RF08 | Fidelização | Consentimento registrado, crédito na entrega e resgate na criação do pedido |
| RF09 | Promoções | Desconto por resgate implementado; campanhas sazonais e segmentação propostas |
| RF10 | Integração de pagamento mock | Aprovação, recusa e indisponibilidade, com registro separado do pedido |
| RF11 | Multicanalidade | `canalPedido`: APP, TOTEM, BALCAO, PICKUP e WEB; registro e filtro na API |
| RF12 | Privacidade | Consulta dos próprios dados, revogação de consentimento, anonimização e auditoria |

## Requisitos não funcionais

| ID | Requisito | Atendimento nesta versão |
| --- | --- | --- |
| RNF01 | Segurança | Autorização por perfil, propriedade do pedido e unidade |
| RNF02 | Integridade | Chaves, restrições, transações e idempotência |
| RNF03 | Contratos da API | Swagger/OpenAPI, erro padronizado e paginação |
| RNF04 | Execução reproduzível | README, ambiente, migrações, carga inicial, Postman e testes |
| RNF05 | Desempenho e disponibilidade | Índices, WAL e paginação; testes de carga e alta disponibilidade pendentes |
| RNF06 | Tolerância a falhas | Timeout mock permite nova tentativa; integração remota e outbox pendentes |

## Prioridades

O fluxo A do roteiro — pedido, pagamento mock e atualização de status — foi priorizado porque permite verificar a integração entre venda, estoque e operação da unidade. A movimentação e a consulta de estoque também permitem demonstrar o fluxo B.

Relatórios financeiros, metas de unidade, campanhas por perfil e disponibilidade sazonal dos produtos não fazem parte da implementação atual. O pagamento é apenas simulado e não recebe dados de cartão.
