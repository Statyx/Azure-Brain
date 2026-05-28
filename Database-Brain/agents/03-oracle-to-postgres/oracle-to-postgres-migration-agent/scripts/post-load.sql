-- post-load.sql — Phase 4: post-data-load fixups.
-- Run with: psql "$PG_CONN" -f post-load.sql
-- Run BEFORE applying indexes/triggers — sequences must reflect current MAX.

\set ON_ERROR_STOP on

-- 1. Advance every sequence to MAX(referenced column) -----------------------
-- Detects sequence ownership via pg_depend, then setval to MAX or 1.
DO $$
DECLARE
  r RECORD;
  max_val BIGINT;
  cmd TEXT;
BEGIN
  FOR r IN
    SELECT
      ns.nspname || '.' || c.relname AS seq_name,
      tab_ns.nspname AS tab_schema,
      tab.relname AS tab_name,
      att.attname AS col_name
    FROM pg_class c
    JOIN pg_namespace ns ON ns.oid = c.relnamespace
    LEFT JOIN pg_depend d ON d.objid = c.oid AND d.deptype = 'a'
    LEFT JOIN pg_class tab ON tab.oid = d.refobjid
    LEFT JOIN pg_namespace tab_ns ON tab_ns.oid = tab.relnamespace
    LEFT JOIN pg_attribute att ON att.attrelid = tab.oid AND att.attnum = d.refobjsubid
    WHERE c.relkind = 'S'
      AND ns.nspname IN ('hr','sh','oe')
  LOOP
    IF r.tab_name IS NULL THEN
      RAISE NOTICE 'Sequence % is orphaned, skipping', r.seq_name;
      CONTINUE;
    END IF;
    cmd := format('SELECT COALESCE(MAX(%I), 0) FROM %I.%I',
                  r.col_name, r.tab_schema, r.tab_name);
    EXECUTE cmd INTO max_val;
    PERFORM setval(r.seq_name, GREATEST(max_val, 1));
    RAISE NOTICE 'setval(%) = %', r.seq_name, GREATEST(max_val, 1);
  END LOOP;
END$$;

-- 2. ANALYZE everything ---------------------------------------------------
ANALYZE;

-- 3. Sanity report --------------------------------------------------------
SELECT n.nspname AS schema,
       c.relname AS table,
       c.reltuples::bigint AS rows_estimate
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind = 'r'
  AND n.nspname IN ('hr','sh','oe')
ORDER BY n.nspname, c.relname;

\echo '==> post-load complete. Next: apply indexes.sql, triggers.sql, then run validate.sh'
