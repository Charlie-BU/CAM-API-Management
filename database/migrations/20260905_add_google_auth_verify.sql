SELECT column_name, is_nullable
FROM information_schema.columns
WHERE table_schema = current_schema()
  AND table_name = 'user'
  AND column_name = 'password';

SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_schema = current_schema()
  AND table_name = 'user_auth_identity'
ORDER BY constraint_name;

SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = current_schema()
  AND tablename = 'user_auth_identity'
ORDER BY indexname;
