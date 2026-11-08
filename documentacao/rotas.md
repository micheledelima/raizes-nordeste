# Contratos da API

Contrato da API: `/openapi.json` e `/docs`, disponíveis ao iniciar o servidor. Valores financeiros em centavos. Listagens usam pagina=1 e limite=10 (1..100). IDs sao UUID. JSON desconhecido e rejeitado. Bearer JWT conforme security em cada operacao; permissoes descritas abaixo e nos summaries. Erro comum: {"erro":{"codigo":"VALIDACAO","mensagem":"Campos invalidos: corpo.canalPedido","requisicaoId":"uuid"}}. Erros: 401 token ausente/invalido, 403 permissao, 404 inexistente, 409 regra, 422 contrato, 503 dependencia. 500 falha interna sem detalhes sensiveis.

## GET /healthcheck

Saude

Acesso: Consulta pública.

Autenticação: Não exige token.

Parâmetros: Nenhum

Entrada:

Sem corpo de requisição.

Resposta 200:

```json
{
  "status": "ok"
}
```

Códigos documentados: 200, 401, 403, 404, 409, 422, 503

## POST /usuarios

Cadastrar cliente

Acesso: Cadastro público. O perfil criado é sempre CLIENTE.

Autenticação: Não exige token.

Parâmetros: Nenhum

Entrada:

```json
{
  "nome": "Maria Silva",
  "email": "maria@example.com",
  "senha": "Senha-local-123!",
  "consentimentoFidelidade": true
}
```

Resposta 201:

```json
{
  "id": "uuid",
  "nome": "Maria Silva",
  "email": "maria@example.com",
  "perfil": "CLIENTE"
}
```

Códigos documentados: 201, 401, 403, 404, 409, 422, 503

## POST /autenticacao/entrar

Autenticar usuario

Acesso: E-mail e senha de uma conta ativa.

Autenticação: Não exige token.

Parâmetros: Nenhum

Entrada:

```json
{
  "email": "cliente@example.com",
  "senha": "senha-definida-no-env"
}
```

Resposta 200:

```json
{
  "tokenAcesso": "jwt",
  "tipoToken": "bearer"
}
```

Códigos documentados: 200, 401, 403, 404, 409, 422, 503

## GET /usuarios/eu

Consultar dados do proprio usuario

Acesso: Usuário autenticado; acesso aos próprios dados.

Autenticação: Bearer JWT.

Parâmetros: Nenhum

Entrada:

Sem corpo de requisição.

Resposta 200:

```json
{
  "id": "uuid",
  "nome": "Maria Silva",
  "email": "maria@example.com",
  "perfil": "CLIENTE",
  "consentimentoFidelidade": true
}
```

Códigos documentados: 200, 401, 403, 404, 409, 422, 503

## DELETE /usuarios/eu

Anonimizar a propria conta

Acesso: Usuário autenticado, sem pedidos em aberto.

Autenticação: Bearer JWT.

Parâmetros: Nenhum

Entrada:

Sem corpo de requisição.

Resposta 204:

Sem conteúdo.

Códigos documentados: 204, 401, 403, 404, 409, 422, 503

## PUT /usuarios/eu/consentimentos

Conceder ou revogar consentimento de fidelidade

Acesso: Usuário autenticado; altera apenas o próprio consentimento.

Autenticação: Bearer JWT.

Parâmetros: Nenhum

Entrada:

```json
{
  "concedido": true
}
```

Resposta 200:

```json
{
  "consentimentoFidelidade": true,
  "versaoPolitica": "1.0"
}
```

Códigos documentados: 200, 401, 403, 404, 409, 422, 503

## GET /unidades

Listar unidades ativas

Acesso: Consulta pública.

Autenticação: Não exige token.

Parâmetros: query:pagina (opcional); query:limite (opcional)

Entrada:

Sem corpo de requisição.

Resposta 200:

```json
{
  "itens": [
    {
      "id": "uuid",
      "nome": "Recife Centro",
      "regiao": "Pernambuco",
      "ativo": 1
    }
  ],
  "pagina": 1,
  "limite": 10,
  "total": 1
}
```

Códigos documentados: 200, 401, 403, 404, 409, 422, 503

## POST /unidades

Cadastrar unidade como administrador

Acesso: ADMIN.

Autenticação: Bearer JWT.

Parâmetros: Nenhum

Entrada:

```json
{
  "nome": "Joao Pessoa Centro",
  "regiao": "Paraiba"
}
```

Resposta 201:

```json
{
  "id": "uuid",
  "nome": "Recife Centro",
  "regiao": "Pernambuco",
  "ativo": 1
}
```

Códigos documentados: 201, 401, 403, 404, 409, 422, 503

## GET /produtos

Listar produtos ativos

Acesso: Consulta pública.

Autenticação: Não exige token.

Parâmetros: query:pagina (opcional); query:limite (opcional)

Entrada:

Sem corpo de requisição.

Resposta 200:

```json
{
  "itens": [
    {
      "id": "20000000-0000-4000-8000-000000000001",
      "nome": "Tapioca de queijo",
      "preco_centavos": 1200,
      "ativo": 1
    }
  ],
  "pagina": 1,
  "limite": 10,
  "total": 1
}
```

Códigos documentados: 200, 401, 403, 404, 409, 422, 503

## POST /produtos

Cadastrar produto como administrador

Acesso: ADMIN.

Autenticação: Bearer JWT.

Parâmetros: Nenhum

Entrada:

```json
{
  "nome": "Bolo de macaxeira",
  "precoCentavos": 900
}
```

Resposta 201:

```json
{
  "id": "20000000-0000-4000-8000-000000000001",
  "nome": "Tapioca de queijo",
  "preco_centavos": 1200,
  "ativo": 1
}
```

Códigos documentados: 201, 401, 403, 404, 409, 422, 503

## GET /unidades/{unidade_id}/cardapio

Consultar cardapio e disponibilidade da unidade

Acesso: Consulta pública.

Autenticação: Não exige token.

Parâmetros: path:unidade_id (obrigatorio); query:pagina (opcional); query:limite (opcional)

Entrada:

Sem corpo de requisição.

Resposta 200:

```json
{
  "itens": [
    {
      "id": "uuid",
      "unidade_id": "10000000-0000-4000-8000-000000000001",
      "produto_id": "20000000-0000-4000-8000-000000000001",
      "quantidade": 100,
      "disponivel": 1,
      "produto": {
        "id": "20000000-0000-4000-8000-000000000001",
        "nome": "Tapioca de queijo",
        "preco_centavos": 1200,
        "ativo": 1
      }
    }
  ],
  "pagina": 1,
  "limite": 10,
  "total": 1
}
```

Códigos documentados: 200, 401, 403, 404, 409, 422, 503

## GET /estoques/{unidade_id}

Consultar estoque como gerente da unidade ou administrador

Acesso: GERENTE da unidade ou ADMIN.

Autenticação: Bearer JWT.

Parâmetros: path:unidade_id (obrigatorio); query:pagina (opcional); query:limite (opcional)

Entrada:

Sem corpo de requisição.

Resposta 200:

```json
{
  "itens": [
    {
      "id": "uuid",
      "unidade_id": "10000000-0000-4000-8000-000000000001",
      "produto_id": "20000000-0000-4000-8000-000000000001",
      "quantidade": 110,
      "disponivel": 1
    }
  ],
  "pagina": 1,
  "limite": 10,
  "total": 1
}
```

Códigos documentados: 200, 401, 403, 404, 409, 422, 503

## POST /estoques/movimentacoes

Movimentar estoque como gerente da unidade ou administrador

Acesso: GERENTE da unidade ou ADMIN.

Autenticação: Bearer JWT.

Parâmetros: Nenhum

Entrada:

```json
{
  "unidadeId": "10000000-0000-4000-8000-000000000001",
  "produtoId": "20000000-0000-4000-8000-000000000001",
  "quantidade": 10,
  "motivo": "Reposicao"
}
```

Resposta 201:

```json
{
  "id": "uuid",
  "unidade_id": "10000000-0000-4000-8000-000000000001",
  "produto_id": "20000000-0000-4000-8000-000000000001",
  "quantidade": 110,
  "disponivel": 1
}
```

Códigos documentados: 201, 401, 403, 404, 409, 422, 503

## POST /pedidos

Criar pedido com reserva de estoque

Acesso: CLIENTE: pedidos proprios. ATENDENTE: unidade vinculada. ADMIN: qualquer unidade. Idempotency-Key obrigatoria; repetir a mesma chave e conteudo devolve o mesmo pedido.

Autenticação: Bearer JWT.

Parâmetros: header:Idempotency-Key (obrigatorio)

Entrada:

```json
{
  "unidadeId": "10000000-0000-4000-8000-000000000001",
  "canalPedido": "TOTEM",
  "itens": [
    {
      "produtoId": "20000000-0000-4000-8000-000000000001",
      "quantidade": 2
    }
  ],
  "pontosResgate": 0
}
```

Resposta 201:

```json
{
  "id": "40000000-0000-4000-8000-000000000001",
  "clienteId": "30000000-0000-4000-8000-000000000001",
  "unidadeId": "10000000-0000-4000-8000-000000000001",
  "canalPedido": "TOTEM",
  "status": "AGUARDANDO_PAGAMENTO",
  "totalCentavos": 2400,
  "descontoCentavos": 0,
  "pontosResgatados": 0,
  "criadoEm": "2026-11-07T12:00:00+00:00",
  "itens": [
    {
      "id": "uuid",
      "pedido_id": "uuid",
      "produto_id": "20000000-0000-4000-8000-000000000001",
      "quantidade": 2,
      "preco_unitario_centavos": 1200
    }
  ]
}
```

Códigos documentados: 201, 401, 403, 404, 409, 422, 503

## GET /pedidos

Listar pedidos com isolamento por cliente ou unidade

Acesso: CLIENTE consulta seus pedidos; equipe consulta a própria unidade; ADMIN consulta a rede.

Autenticação: Bearer JWT.

Parâmetros: query:pagina (opcional); query:limite (opcional); query:canalPedido (opcional); query:status (opcional)

Entrada:

Sem corpo de requisição.

Resposta 200:

```json
{
  "itens": [
    {
      "id": "40000000-0000-4000-8000-000000000001",
      "clienteId": "30000000-0000-4000-8000-000000000001",
      "unidadeId": "10000000-0000-4000-8000-000000000001",
      "canalPedido": "TOTEM",
      "status": "AGUARDANDO_PAGAMENTO",
      "totalCentavos": 2400,
      "descontoCentavos": 0,
      "pontosResgatados": 0,
      "criadoEm": "2026-11-07T12:00:00+00:00",
      "itens": [
        {
          "id": "uuid",
          "pedido_id": "uuid",
          "produto_id": "20000000-0000-4000-8000-000000000001",
          "quantidade": 2,
          "preco_unitario_centavos": 1200
        }
      ]
    }
  ],
  "pagina": 1,
  "limite": 10,
  "total": 1
}
```

Códigos documentados: 200, 401, 403, 404, 409, 422, 503

## GET /pedidos/{pedido_id}

Consultar pedido proprio ou da unidade

Acesso: CLIENTE proprietário, funcionário da unidade ou ADMIN.

Autenticação: Bearer JWT.

Parâmetros: path:pedido_id (obrigatorio)

Entrada:

Sem corpo de requisição.

Resposta 200:

```json
{
  "id": "40000000-0000-4000-8000-000000000001",
  "clienteId": "30000000-0000-4000-8000-000000000001",
  "unidadeId": "10000000-0000-4000-8000-000000000001",
  "canalPedido": "TOTEM",
  "status": "AGUARDANDO_PAGAMENTO",
  "totalCentavos": 2400,
  "descontoCentavos": 0,
  "pontosResgatados": 0,
  "criadoEm": "2026-11-07T12:00:00+00:00",
  "itens": [
    {
      "id": "uuid",
      "pedido_id": "uuid",
      "produto_id": "20000000-0000-4000-8000-000000000001",
      "quantidade": 2,
      "preco_unitario_centavos": 1200
    }
  ]
}
```

Códigos documentados: 200, 401, 403, 404, 409, 422, 503

## PATCH /pedidos/{pedido_id}/status

Atualizar status respeitando o fluxo operacional

Acesso: PRONTO: cozinha, gerente ou admin. ENTREGUE: atendente, gerente ou admin. CANCELADO: cliente antes do pagamento; atendente, gerente ou admin antes de pronto. Funcionarios restritos a unidade vinculada.

Autenticação: Bearer JWT.

Parâmetros: path:pedido_id (obrigatorio)

Entrada:

```json
{
  "status": "PRONTO"
}
```

Resposta 200:

```json
{
  "id": "40000000-0000-4000-8000-000000000001",
  "clienteId": "30000000-0000-4000-8000-000000000001",
  "unidadeId": "10000000-0000-4000-8000-000000000001",
  "canalPedido": "TOTEM",
  "status": "PRONTO",
  "totalCentavos": 2400,
  "descontoCentavos": 0,
  "pontosResgatados": 0,
  "criadoEm": "2026-11-07T12:00:00+00:00",
  "itens": [
    {
      "id": "uuid",
      "pedido_id": "uuid",
      "produto_id": "20000000-0000-4000-8000-000000000001",
      "quantidade": 2,
      "preco_unitario_centavos": 1200
    }
  ]
}
```

Códigos documentados: 200, 401, 403, 404, 409, 422, 503

## POST /pagamentos

Solicitar e registrar pagamento mock

Acesso: CLIENTE proprietario, ATENDENTE da unidade ou ADMIN. APROVADO inicia preparo; RECUSADO cancela e devolve estoque; TEMPO_ESGOTADO retorna 503 sem finalizar. Repeticao do mesmo resultado nao duplica pagamento.

Autenticação: Bearer JWT.

Parâmetros: Nenhum

Entrada:

```json
{
  "pedidoId": "40000000-0000-4000-8000-000000000001",
  "resultado": "APROVADO"
}
```

Resposta 201:

```json
{
  "pagamento": {
    "id": "uuid",
    "pedido_id": "40000000-0000-4000-8000-000000000001",
    "status": "APROVADO",
    "valor_centavos": 2400,
    "criado_em": "2026-11-07T12:00:00+00:00",
    "retorno": {
      "provedor": "SIMULADO",
      "referencia": "simulado-uuid",
      "status": "APROVADO",
      "valorCentavos": 2400,
      "mensagem": "Pagamento simulado aprovado."
    }
  },
  "pedido": {
    "id": "40000000-0000-4000-8000-000000000001",
    "clienteId": "30000000-0000-4000-8000-000000000001",
    "unidadeId": "10000000-0000-4000-8000-000000000001",
    "canalPedido": "TOTEM",
    "status": "EM_PREPARO",
    "totalCentavos": 2400,
    "descontoCentavos": 0,
    "pontosResgatados": 0,
    "criadoEm": "2026-11-07T12:00:00+00:00",
    "itens": [
      {
        "id": "uuid",
        "pedido_id": "uuid",
        "produto_id": "20000000-0000-4000-8000-000000000001",
        "quantidade": 2,
        "preco_unitario_centavos": 1200
      }
    ]
  }
}
```

Códigos documentados: 201, 401, 403, 404, 409, 422, 503

## GET /fidelidade

Consultar saldo e historico do proprio usuario

Acesso: Usuário autenticado; saldo e histórico da própria conta.

Autenticação: Bearer JWT.

Parâmetros: query:pagina (opcional); query:limite (opcional)

Entrada:

Sem corpo de requisição.

Resposta 200:

```json
{
  "saldo": 24,
  "consentimento": true,
  "historico": {
    "itens": [],
    "pagina": 1,
    "limite": 10,
    "total": 0
  }
}
```

Códigos documentados: 200, 401, 403, 404, 409, 422, 503

## GET /auditorias

Consultar auditoria como administrador

Acesso: ADMIN.

Autenticação: Bearer JWT.

Parâmetros: query:pagina (opcional); query:limite (opcional)

Entrada:

Sem corpo de requisição.

Resposta 200:

```json
{
  "itens": [
    {
      "id": "uuid",
      "ator_id": "uuid",
      "acao": "PEDIDO_CRIADO",
      "recurso_id": "uuid",
      "criado_em": "2026-11-07T12:00:00+00:00"
    }
  ],
  "pagina": 1,
  "limite": 10,
  "total": 1
}
```

Códigos documentados: 200, 401, 403, 404, 409, 422, 503
