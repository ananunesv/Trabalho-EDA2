-- NewsGraph — schema v2.1
-- Rodar UMA vez: SQL Editor do Supabase ou `psql "$DATABASE_URL" -f persistencia/init_db.sql`.
-- ATENÇÃO: se o banco já existia na v2.0, use persistencia/migracao_escopo.sql em vez deste.

CREATE TABLE IF NOT EXISTS usuarios (
  id          SERIAL PRIMARY KEY,
  nome        TEXT NOT NULL,
  criado_em   TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS noticias (
  id               SERIAL PRIMARY KEY,
  titulo           TEXT NOT NULL,
  resumo           TEXT,
  link             TEXT UNIQUE NOT NULL,          -- chave de deduplicação
  fonte            TEXT,
  data_publicacao  TIMESTAMP,
  coletado_em      TIMESTAMP DEFAULT now(),
  -- Issue #3: filtro de escopo financeiro
  score_economico  INT     NOT NULL DEFAULT 0,    -- nº de sinais econômicos detectados
  em_escopo        BOOLEAN NOT NULL DEFAULT TRUE  -- FALSE = excluída do grafo
);

CREATE TABLE IF NOT EXISTS interacoes (
  id          SERIAL PRIMARY KEY,
  usuario_id  INT REFERENCES usuarios(id),
  noticia_id  INT REFERENCES noticias(id),
  tipo_acao   TEXT CHECK (tipo_acao IN ('clique','like','compartilhar','dislike')),
  peso        INT NOT NULL,                        -- clique 1, like 4, compartilhar 5, dislike -3
  timestamp   TIMESTAMP DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_interacoes_usuario ON interacoes(usuario_id);
CREATE INDEX IF NOT EXISTS idx_interacoes_noticia ON interacoes(noticia_id);
-- Index para acelerar a query WHERE em_escopo = TRUE usada pelo grafo
CREATE INDEX IF NOT EXISTS idx_noticias_escopo    ON noticias(em_escopo);