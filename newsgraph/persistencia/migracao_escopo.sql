-- NewsGraph — migração v2.0 → v2.1 (Issue #3: filtro de escopo)
-- Execute UMA VEZ no banco existente:
--   psql "$DATABASE_URL" -f persistencia/migracao_escopo.sql
-- Ou cole no SQL Editor do Supabase.
--
-- É seguro rodar em banco com dados: usa IF NOT EXISTS / ON CONFLICT.
-- Não apaga nada — apenas acrescenta colunas e o index.

ALTER TABLE noticias
  ADD COLUMN IF NOT EXISTS score_economico INT     NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS em_escopo        BOOLEAN NOT NULL DEFAULT TRUE;

CREATE INDEX IF NOT EXISTS idx_noticias_escopo ON noticias(em_escopo);

-- Confirma o resultado
SELECT column_name, data_type, column_default
FROM   information_schema.columns
WHERE  table_name = 'noticias'
  AND  column_name IN ('score_economico', 'em_escopo');