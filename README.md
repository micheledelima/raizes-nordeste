# Raízes do Nordeste

Projeto de API para a rede de lanchonetes Raízes do Nordeste.

## Estrutura

- `src/raizes/domain`: entidades e regras de negócio.
- `src/raizes/application`: casos de uso e contratos de serviços.
- `src/raizes/infrastructure`: persistência e integrações.
- `src/raizes/api`: rotas e contratos HTTP.

## Ambiente de desenvolvimento

Python 3.13 ou superior.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[desenvolvimento]"
Copy-Item .env.example .env
```

Configure as variáveis em `.env` e mantenha esse arquivo fora do versionamento.

## Banco de dados

O projeto usa SQLite, incluído no Python. Configure o caminho do banco em `.env`:

```dotenv
RAIZES_BANCO_DADOS=dados/raizes.db
```

Aplique a migração inicial:

```powershell
.\.venv\Scripts\python -m raizes.linha_comando migrar
```

O comando cria a pasta, o banco e o esquema. Repetir o comando preserva os registros e não reaplica migrações já registradas.

A migração define usuários, unidades, produtos, estoque, pedidos, itens, pagamentos, movimentações, fidelidade, consentimentos e auditoria. Inclui chaves estrangeiras, índices e restrições de integridade. O repositório permite consultas e gravações dentro de transações, com confirmação ao concluir e rollback em caso de erro.

## Testes

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m ruff check src testes
```

## Catálogo e estoque

Após aplicar a migração, cadastre unidades e produtos pela API com uma conta ADMIN. As rotas públicas `GET /unidades`, `GET /produtos` e `GET /unidades/{unidadeId}/cardapio` permitem a consulta do catálogo. As rotas de criação e movimentação de estoque exigem autenticação; apenas ADMIN e GERENTE podem consultar ou alterar estoque, respeitando a unidade vinculada ao usuário.

Para dados locais de demonstração, defina `RAIZES_SENHA_INICIAL` no `.env` e execute:

```powershell
.\.venv\Scripts\python -m raizes.linha_comando popular
```

O comando cadastra duas unidades, dois produtos, estoque inicial e contas de exemplo sem sobrescrever registros existentes.
## Pedidos e pagamentos

Clientes, atendentes e administradores criam pedidos em `POST /pedidos` com `unidadeId`, `canalPedido` e itens. Os canais aceitos são `APP`, `TOTEM`, `BALCAO`, `PICKUP` e `WEB`. A requisição exige o cabeçalho `Idempotency-Key`; a mesma chave com o mesmo conteúdo devolve o pedido já criado. O estoque é reservado na criação.

`POST /pagamentos` registra um pagamento simulado aprovado, recusado ou com tempo esgotado. Um pagamento aprovado encaminha o pedido para preparo; um pagamento recusado cancela o pedido e devolve o estoque. COZINHA marca o pedido como pronto e ATENDENTE registra a entrega.
## Cadastro e autenticação

Configure `RAIZES_SEGREDO_JWT` em `.env` com uma chave aleatória de pelo menos 32 caracteres. O valor `segredo` do arquivo de exemplo precisa ser substituído para executar esta etapa. Uma chave pode ser gerada com:

```powershell
.\.venv\Scripts\python -c "import secrets; print(secrets.token_urlsafe(48))"
```

`RAIZES_DURACAO_TOKEN_MINUTOS` define a validade do token, com padrão de 30 minutos. Depois de aplicar a migração, inicie a API:

```powershell
.\.venv\Scripts\python -m uvicorn raizes.montagem:montar_api --factory --reload
```

Swagger: http://127.0.0.1:8000/docs. Contrato OpenAPI: http://127.0.0.1:8000/openapi.json.

| Método | Rota | Acesso |
| --- | --- | --- |
| GET | `/healthcheck` | Público |
| POST | `/usuarios` | Público; cria apenas CLIENTE |
| POST | `/autenticacao/entrar` | E-mail e senha |
| GET | `/usuarios/eu` | Token Bearer válido; dados da própria conta |

Exemplo de cadastro:

```json
{
  "nome": "Maria Silva",
  "email": "maria@example.com",
  "senha": "Senha-de-teste-123!"
}
```

A senha deve ter entre 12 e 128 caracteres. O e-mail é normalizado para minúsculas e não pode ser cadastrado duas vezes. As senhas são armazenadas com hash scrypt e sal aleatório.

Envie `email` e `senha` para `/autenticacao/entrar`. A resposta contém `tokenAcesso` e `tipoToken`. Use o token em `Authorization: Bearer <token>` para consultar `/usuarios/eu`. O JWT valida assinatura, validade, emissor e destinatário. Contas desativadas perdem o acesso mesmo com token ainda válido.

Os perfis são CLIENTE, ATENDENTE, COZINHA, GERENTE e ADMIN. O cadastro público não aceita a escolha de perfil. A verificação de permissões fica no domínio. Cadastro, login e consulta de dados pessoais geram registros de auditoria.

Falhas seguem o formato `{"erro":{"codigo":"NAO_AUTENTICADO","mensagem":"Informe um token Bearer valido.","requisicaoId":"uuid"}}`. Dados inválidos retornam 422; e-mail duplicado, 409; credenciais ou token inválidos, 401. Os testes cobrem também a rejeição de perfil sem permissão com 403.
