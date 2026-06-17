-- NewsGraph — schema v2.0
-- Rodar UMA vez: SQL Editor do Supabase ou `psql "$DATABASE_URL" -f persistencia/init_db.sql`.

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
  coletado_em      TIMESTAMP DEFAULT now()
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
