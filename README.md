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
