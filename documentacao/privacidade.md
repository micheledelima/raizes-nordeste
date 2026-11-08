# Privacidade e segurança

## Dados tratados

| Dado | Finalidade | Base legal proposta | Proteção |
| --- | --- | --- | --- |
| Nome e e-mail | Identificação da conta e operação do pedido | Execução contratual | Consulta pelo titular e anonimização |
| Hash de senha | Autenticação | Vinculada à operação e proteção da conta | scrypt com salt aleatório; hash não retornado pela API |
| Pedidos e pagamentos mock | Atendimento e rastreabilidade | Execução contratual e obrigações aplicáveis | Acesso restrito ao cliente ou à equipe autorizada |
| Consentimento de fidelidade | Acúmulo e resgate de pontos | Consentimento específico | Registro de data, finalidade, versão e revogação |
| Auditoria | Apuração de operações sensíveis | Interesse legítimo ou obrigação aplicável | Consulta restrita a ADMIN; sem conteúdo das requisições |

As bases legais precisam de validação pelo controlador antes de uso em produção. Os controles descritos aqui são os implementados no protótipo e não representam uma avaliação jurídica completa.

O cadastro não solicita CPF, telefone, endereço, idade ou dados de cartão. A participação na fidelidade é opcional. `PUT /usuarios/eu/consentimentos` registra cada concessão ou revogação com data em UTC, finalidade `FIDELIDADE` e versão `1.0` da política.

## Autenticação e acesso

As senhas usam scrypt com N=16384, r=8, p=1 e salt aleatório de 16 bytes. O JWT usa HS256, chave externa com pelo menos 32 caracteres e duração padrão de 30 minutos. A validação confere assinatura, expiração, emissor e destinatário.

A aplicação verifica o usuário a cada requisição. Contas desativadas deixam de ter acesso mesmo com token ainda dentro da validade. Também são conferidos perfil, propriedade do pedido e unidade do funcionário. Refresh token, logout com revogação e lista de tokens bloqueados ainda não foram implementados.

## Auditoria

São registrados cadastro, login bem-sucedido, consulta de dados pessoais, consentimento, anonimização, estoque, criação de pedido, pagamento e mudança de status. A consulta à auditoria exige ADMIN e também gera registro.

Os registros guardam identificador do ator, ação, recurso e data. Senhas, tokens, e-mails e corpos de requisição não entram nos logs técnicos.

## Anonimização e retenção

`DELETE /usuarios/eu` substitui nome e e-mail, inutiliza a senha, desativa a conta e zera os pontos. A operação é bloqueada enquanto houver pedido em aberto.

Identificadores técnicos e transações permanecem para preservar o histórico e as relações do banco. Dados contextuais ainda podem permitir reidentificação; a substituição dos campos não garante anonimato absoluto.

Não há expurgo automático. A proposta é revisar a necessidade dos logs após 180 dias e definir prazos para contas inativas, transações e backups conforme a política do controlador e as obrigações aplicáveis.

## Antes de publicar em produção

Configurar HTTPS, limitação de tentativas de login, gestão de segredos, backups cifrados, monitoramento e atendimento aos titulares. As contas demonstrativas do seed são destinadas ao ambiente local.
