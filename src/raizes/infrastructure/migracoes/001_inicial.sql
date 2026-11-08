CREATE TABLE "unidades" (id TEXT PRIMARY KEY, nome TEXT NOT NULL, regiao TEXT NOT NULL, ativo INTEGER NOT NULL DEFAULT 1);

CREATE TABLE "usuarios" (
 id TEXT PRIMARY KEY, nome TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
 senha_hash TEXT NOT NULL, perfil TEXT NOT NULL CHECK(perfil IN ('CLIENTE','ATENDENTE','COZINHA','GERENTE','ADMIN')),
 unidade_id TEXT REFERENCES "unidades"(id), consentimento INTEGER NOT NULL DEFAULT 0 CHECK(consentimento IN (0,1)),
 pontos INTEGER NOT NULL DEFAULT 0 CHECK(pontos >= 0), ativo INTEGER NOT NULL DEFAULT 1,
 versao_token INTEGER NOT NULL DEFAULT 0, criado_em TEXT NOT NULL
);

CREATE TABLE "produtos" (id TEXT PRIMARY KEY, nome TEXT NOT NULL, preco_centavos INTEGER NOT NULL CHECK(preco_centavos > 0), ativo INTEGER NOT NULL DEFAULT 1);

CREATE TABLE "estoques" (
 id TEXT PRIMARY KEY, unidade_id TEXT NOT NULL REFERENCES "unidades"(id), produto_id TEXT NOT NULL REFERENCES "produtos"(id),
 quantidade INTEGER NOT NULL DEFAULT 0 CHECK(quantidade >= 0), disponivel INTEGER NOT NULL DEFAULT 1,
 UNIQUE(unidade_id, produto_id)
);

CREATE TABLE "pedidos" (
 id TEXT PRIMARY KEY, usuario_id TEXT NOT NULL REFERENCES "usuarios"(id), unidade_id TEXT NOT NULL REFERENCES "unidades"(id),
 canal TEXT NOT NULL CHECK(canal IN ('APP','TOTEM','BALCAO','PICKUP','WEB')),
 status TEXT NOT NULL CHECK(status IN ('AGUARDANDO_PAGAMENTO','EM_PREPARO','PRONTO','ENTREGUE','CANCELADO')),
 total_centavos INTEGER NOT NULL CHECK(total_centavos >= 0), desconto_centavos INTEGER NOT NULL DEFAULT 0,
 pontos_resgatados INTEGER NOT NULL DEFAULT 0, chave_idempotencia TEXT NOT NULL,
 resumo_requisicao TEXT NOT NULL, criado_em TEXT NOT NULL, UNIQUE(usuario_id, chave_idempotencia)
);

CREATE TABLE "itens_pedido" (
 id TEXT PRIMARY KEY, pedido_id TEXT NOT NULL REFERENCES "pedidos"(id), produto_id TEXT NOT NULL REFERENCES "produtos"(id),
 quantidade INTEGER NOT NULL CHECK(quantidade > 0), preco_unitario_centavos INTEGER NOT NULL CHECK(preco_unitario_centavos > 0),
 UNIQUE(pedido_id, produto_id)
);

CREATE TABLE "pagamentos" (
 id TEXT PRIMARY KEY, pedido_id TEXT NOT NULL UNIQUE REFERENCES "pedidos"(id), status TEXT NOT NULL,
 valor_centavos INTEGER NOT NULL CHECK(valor_centavos >= 0), retorno TEXT NOT NULL, criado_em TEXT NOT NULL
);

CREATE TABLE "movimentacoes_estoque" (
 id TEXT PRIMARY KEY, unidade_id TEXT NOT NULL REFERENCES "unidades"(id), produto_id TEXT NOT NULL REFERENCES "produtos"(id),
 variacao INTEGER NOT NULL CHECK(variacao != 0), motivo TEXT NOT NULL, ator_id TEXT NOT NULL REFERENCES "usuarios"(id), criado_em TEXT NOT NULL
);

CREATE TABLE "eventos_fidelidade" (
 id TEXT PRIMARY KEY, usuario_id TEXT NOT NULL REFERENCES "usuarios"(id), pedido_id TEXT REFERENCES "pedidos"(id),
 variacao INTEGER NOT NULL, tipo TEXT NOT NULL, criado_em TEXT NOT NULL, UNIQUE(pedido_id, tipo)
);

CREATE TABLE "consentimentos" (
 id TEXT PRIMARY KEY, usuario_id TEXT NOT NULL REFERENCES "usuarios"(id), concedido INTEGER NOT NULL CHECK(concedido IN (0,1)),
 finalidade TEXT NOT NULL, versao_politica TEXT NOT NULL, criado_em TEXT NOT NULL
);

CREATE TABLE "registros_auditoria" (
 id TEXT PRIMARY KEY, ator_id TEXT NOT NULL REFERENCES "usuarios"(id), acao TEXT NOT NULL,
 recurso_id TEXT NOT NULL, criado_em TEXT NOT NULL
);

CREATE INDEX idx_auditoria_ator ON registros_auditoria(ator_id);

CREATE INDEX idx_movimentacoes_estoque_unidade ON movimentacoes_estoque(unidade_id);

CREATE INDEX idx_pedidos_unidade_canal_status ON pedidos(unidade_id, canal, status);

CREATE INDEX idx_pedidos_usuario ON pedidos(usuario_id);
