# PostgreSQL Legacy Migration Guide

## Target
- File: `20260409_postgres_legacy_schema_to_delivery_issue.sql`
- Purpose: migrate legacy schema (`student_name`, `course_interest`, `learning_goal`, `student_question`, `assessments`) to current delivery-issue schema.

## Before You Run
1. Take a DB backup.
2. Stop application writes (maintenance window recommended).
3. Verify you are connected to the right database.

## Run
```bash
psql "$APP_DATABASE_URL" -v ON_ERROR_STOP=1 -f backend/sql/migrations/20260409_postgres_legacy_schema_to_delivery_issue.sql
```

## Post-Run Quick Checks
```sql
-- expected new columns
SELECT column_name
FROM information_schema.columns
WHERE table_schema='public' AND table_name='leads'
ORDER BY ordinal_position;

SELECT column_name
FROM information_schema.columns
WHERE table_schema='public' AND table_name='calls'
ORDER BY ordinal_position;

-- migrated analyses row count
SELECT COUNT(*) AS incident_analyses_count FROM public.incident_analyses;
```

## Notes
- The migration is idempotent (safe to re-run).
- Legacy `assessments` rows are copied into `incident_analyses` with `ON CONFLICT DO NOTHING`.
- The legacy `assessments` table is not dropped automatically.
