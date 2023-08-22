CREATE EXTENSION pg_trgm;

-- CREATE OR REPLACE FUNCTION array_to_string_immutable(
--     anyarray,
--     varchar
-- ) RETURNS text LANGUAGE sql IMMUTABLE AS $$
--     SELECT array_to_string($1, $2)
-- $$;
-- array_to_string_immutable(stack, ' ')

CREATE TABLE IF NOT EXISTS pessoa (
    id VARCHAR(36),
    apelido VARCHAR(32) CONSTRAINT APELIDO_PK PRIMARY KEY,
    nome VARCHAR(100),
    nascimento CHAR(10),
    stack VARCHAR(1024),
    busca VARCHAR GENERATED ALWAYS AS (
        apelido || ' ' || nome || ' ' || stack
    ) STORED
);


CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pessoa_busca_gist ON pessoa USING GIST (busca gist_trgm_ops);
