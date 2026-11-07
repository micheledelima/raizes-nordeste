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
