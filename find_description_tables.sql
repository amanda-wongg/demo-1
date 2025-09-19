-- Query 1: Find tables that might contain bank transaction descriptions
SELECT table_schema, table_name, column_name
FROM information_schema.columns 
WHERE column_name ILIKE '%description%' 
   OR column_name ILIKE '%memo%'
   OR column_name ILIKE '%reference%'
   OR column_name ILIKE '%narrative%'
ORDER BY table_schema, table_name;

-- Query 2: Look for tables with "bank" or "transaction" in the name
SELECT table_schema, table_name
FROM information_schema.tables 
WHERE (table_name ILIKE '%bank%' OR table_name ILIKE '%transaction%')
  AND table_schema IN ('zenpayroll_production', 'bi', 'banking')
ORDER BY table_schema, table_name;

-- Query 3: Check what fields are available to join on
SELECT column_name, data_type
FROM information_schema.columns 
WHERE table_name = 'bank_transactions' 
  AND table_schema = 'bi'
  AND (column_name ILIKE '%id%' OR column_name ILIKE '%external%')
ORDER BY column_name;