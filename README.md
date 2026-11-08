# Raízes do Nordeste

API REST Python para operação de uma rede de lanchonetes, com pedidos multicanal, estoque por unidade, pagamento simulado e fidelidade mediante consentimento.

## Requisitos

Python 3.13 ou superior. SQLite integrado ao Python. PowerShell para os comandos abaixo. As dependências diretas estão fixadas em `pyproject.toml`; `requirements.lock` registra também as transitivas.

## Execução local

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.lock
.\.venv\Scripts\python -m pip install --no-deps -e .
Copy-Item .env.example .env
.\.venv\Scripts\python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Edite `.env`: substitua `RAIZES_SEGREDO_JWT` pela chave gerada e `RAIZES_SENHA_INICIAL` por uma senha local com pelo menos 12 caracteres. Não publique `.env`. A configuração lê esse arquivo automaticamente; variáveis do processo têm precedência.

```powershell
.\.venv\Scripts\python -m raizes.linha_comando migrar
.\.venv\Scripts\python -m raizes.linha_comando popular
.\.venv\Scripts\python -m uvicorn raizes.montagem:montar_api --factory --reload
```

O comando cria a pasta, o banco e o esquema. Repetir o comando preserva os registros e não reaplica migrações já registradas.

A carga inicial pode ser repetida e não sobrescreve saldos, senhas ou contas existentes. Crie o banco antes de iniciar a API.

Swagger: http://127.0.0.1:8000/docs. OpenAPI: http://127.0.0.1:8000/openapi.json. Saúde: http://127.0.0.1:8000/healthcheck. O contrato é gerado pela API em execução.

## Dados demonstrativos

A carga inicial cria duas unidades e dois produtos. Cada produto começa com 100 unidades em cada loja. IDs estáveis:

| Recurso | ID |
| --- | --- |
| Recife Centro | 10000000-0000-4000-8000-000000000001 |
| Natal Centro | 10000000-0000-4000-8000-000000000002 |
| Tapioca de queijo, R$ 12,00 | 20000000-0000-4000-8000-000000000001 |
| Cuscuz recheado, R$ 18,00 | 20000000-0000-4000-8000-000000000002 |

Contas locais: `cliente@example.com`, `atendente@example.com`, `cozinha@example.com`, `gerente@example.com`, `admin@example.com`. Todas usam a senha escolhida em `RAIZES_SENHA_INICIAL`. Os funcionários cadastrados inicialmente pertencem à unidade Recife Centro. O administrador tem acesso às demais unidades. O cadastro público cria apenas contas CLIENTE.

## Testes e qualidade

```powershell
.\.venv\Scripts\python -m pytest -q --junitxml=documentacao/evidencias/pytest.xml
.\.venv\Scripts\python -m ruff check src testes
.\.venv\Scripts\python -m ruff format --check src testes
```

Os testes usam bancos temporários. Os resultados das execuções ficam em `documentacao/evidencias`.

## Arquitetura

`domain` contém perfis, canais e transições de pedido. `application` orquestra casos de uso e define portas. `infrastructure` implementa repositório SQLite, migrações, hash scrypt, JWT e pagamento simulado. `api` adapta HTTP e valida contratos. `montagem.py` monta as dependências. O domínio não importa framework ou banco; a aplicação depende de portas, sem SQL.

A transação de criação inclui estoque, pedido, itens, pontos e auditoria. SQLite usa WAL e transações de escrita serializadas, com espera limitada. O teste concorrente verifica que duas compras não vendem o mesmo saldo. O pagamento simulado é local e determinístico. Uma integração externa precisará de uma caixa de saída transacional, confirmação autenticada, reconciliação e novas tentativas fora da transação. Testes de carga e de alta disponibilidade estão pendentes.

## Documentação e entrega

- [Requisitos e decisões](documentacao/requisitos.md)
- [Arquitetura, regras e fluxo crítico](documentacao/arquitetura.md)
- [Contratos das rotas](documentacao/rotas.md)
- [Privacidade e segurança](documentacao/privacidade.md)

Repositório: https://github.com/micheledelima/raizes-nordeste. O `origin` está configurado para esse endereço. Os arquivos ainda estão apenas na pasta local, sem commits ou envio para o GitHub.

Referências técnicas: [FastAPI](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/), [SQLite no Python](https://docs.python.org/3.13/library/sqlite3.html), [PyJWT](https://pyjwt.readthedocs.io/en/stable/). O escopo segue o estudo de caso da rede e o roteiro da trilha Back-End de 2026.

## Nomes e atualização do banco

A migração `001_inicial.sql` cria o esquema em português. Com o ambiente virtual ativo, execute `python -m raizes.linha_comando migrar` antes de iniciar a API. As próximas mudanças de esquema devem entrar em novos arquivos de migração.

O projeto usa nomes em português. Identificadores exigidos pelo Python e pelas bibliotecas, formatos OpenAPI/Postman e os valores de canal definidos no roteiro (`APP`, `TOTEM`, `BALCAO`, `PICKUP`, `WEB`) mantêm a grafia exigida por esses contratos.

A autenticação está em `/autenticacao/entrar`; o perfil próprio, em `/usuarios/eu`; e a verificação de saúde, em `/healthcheck`. O login devolve `tokenAcesso` e `tipoToken`. As listagens usam `pagina`, `limite`, `itens` e `total`. O erro inclui `requisicaoId`. As versões anteriores desses nomes não são mantidas como rotas alternativas.

O banco local fica em `dados/raizes.db`, conforme `RAIZES_BANCO_DADOS`. Os demais parâmetros são `RAIZES_SEGREDO_JWT`, `RAIZES_DURACAO_TOKEN_MINUTOS` e `RAIZES_SENHA_INICIAL`.
