# Privacidade e segurança

## Dados utilizados

| Dado | Uso no sistema | Proteção aplicada |
| --- | --- | --- |
| Nome e e-mail | Cadastro e identificação da conta | Consulta apenas pelo titular; anonimização disponível |
| Senha | Autenticação | Hash scrypt com sal aleatório |
| Pedidos | Atendimento e histórico | Acesso pelo cliente ou equipe autorizada |
| Consentimento | Participação na fidelidade | Registro de data, finalidade e versão |
| Auditoria | Registro de ações importantes | Consulta restrita a ADMIN |

O sistema não solicita CPF, telefone, endereço ou dados de cartão.

## Autenticação e acesso

As senhas não são retornadas pela API. O JWT usa chave configurada no ambiente e expira conforme `RAIZES_DURACAO_TOKEN_MINUTOS`. A cada requisição autenticada, a aplicação confere se a conta está ativa.

As permissões consideram o perfil, o dono do pedido e a unidade do funcionário. Um gerente não acessa estoque ou pedidos de outra unidade.

## Consentimento e anonimização

O consentimento de fidelidade pode ser alterado em `PUT /usuarios/eu/consentimentos`. Sem consentimento, não há crédito nem resgate de pontos.

`DELETE /usuarios/eu` substitui nome e e-mail, invalida a senha, desativa a conta e remove o saldo de pontos. Pedidos e registros técnicos permanecem para manter a integridade do histórico.

## Auditoria

São registrados cadastro, login, alteração de consentimento, anonimização, estoque, pedido, pagamento e mudança de status. Os registros guardam ator, ação, recurso e data. Senhas, tokens e corpo das requisições não são registrados.

## Limites atuais

O projeto é acadêmico e usa banco local. HTTPS, limitação de tentativas, backups e política de retenção precisam ser definidos antes de uso fora desse ambiente.
