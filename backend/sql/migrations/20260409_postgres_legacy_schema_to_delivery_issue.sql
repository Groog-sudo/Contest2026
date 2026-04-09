-- Migration: Legacy PostgreSQL schema -> Delivery Issue schema
-- Date: 2026-04-09
-- Safe to re-run (idempotent)
--
-- What this migration does:
-- 1) Moves legacy column names to the new domain naming
--    leads: student_name -> customer_name
--           course_interest -> order_id
--           learning_goal -> incident_summary
--           preferred_call_time -> preferred_contact_time
--    calls: student_question -> incident_summary
-- 2) Creates incident_analyses table (if missing)
-- 3) Copies legacy assessments rows into incident_analyses (deduplicated by PK)
-- 4) Ensures required tables and indexes used by current backend exist

BEGIN;

-- 1) Ensure base tables exist (new naming)
CREATE TABLE IF NOT EXISTS public.leads (
    lead_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    order_id TEXT NOT NULL,
    incident_summary TEXT NOT NULL,
    preferred_contact_time TEXT,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS public.calls (
    call_id TEXT PRIMARY KEY,
    lead_id TEXT NOT NULL,
    incident_summary TEXT NOT NULL,
    status TEXT NOT NULL,
    script_preview TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS public.call_transcript_turns (
    turn_id TEXT PRIMARY KEY,
    transcript_id TEXT NOT NULL,
    call_id TEXT NOT NULL,
    lead_id TEXT NOT NULL,
    speaker TEXT NOT NULL,
    utterance TEXT NOT NULL,
    turn_index INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS public.knowledge_documents (
    document_id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    status TEXT NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS public.knowledge_document_chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    title TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    UNIQUE(document_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS public.recordings (
    recording_id TEXT PRIMARY KEY,
    call_id TEXT NOT NULL,
    lead_id TEXT NOT NULL,
    object_key TEXT NOT NULL,
    content_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS public.async_tasks (
    task_id TEXT PRIMARY KEY,
    task_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    status TEXT NOT NULL,
    result_json TEXT,
    error_message TEXT,
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

-- 2) Legacy -> new column migration for leads
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'student_name'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'customer_name'
    ) THEN
        EXECUTE 'ALTER TABLE public.leads RENAME COLUMN student_name TO customer_name';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'student_name'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'customer_name'
    ) THEN
        EXECUTE 'UPDATE public.leads SET customer_name = COALESCE(customer_name, student_name)';
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'course_interest'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'order_id'
    ) THEN
        EXECUTE 'ALTER TABLE public.leads RENAME COLUMN course_interest TO order_id';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'course_interest'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'order_id'
    ) THEN
        EXECUTE 'UPDATE public.leads SET order_id = COALESCE(order_id, course_interest)';
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'learning_goal'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'incident_summary'
    ) THEN
        EXECUTE 'ALTER TABLE public.leads RENAME COLUMN learning_goal TO incident_summary';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'learning_goal'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'incident_summary'
    ) THEN
        EXECUTE 'UPDATE public.leads SET incident_summary = COALESCE(incident_summary, learning_goal)';
    END IF;

    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'preferred_call_time'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'preferred_contact_time'
    ) THEN
        EXECUTE 'ALTER TABLE public.leads RENAME COLUMN preferred_call_time TO preferred_contact_time';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'preferred_call_time'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'preferred_contact_time'
    ) THEN
        EXECUTE 'UPDATE public.leads SET preferred_contact_time = COALESCE(preferred_contact_time, preferred_call_time)';
    END IF;

    ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS customer_name TEXT;
    ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS phone_number TEXT;
    ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS order_id TEXT;
    ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS incident_summary TEXT;
    ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS preferred_contact_time TEXT;
    ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ;
END $$;

-- 3) Legacy -> new column migration for calls
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'calls' AND column_name = 'student_question'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'calls' AND column_name = 'incident_summary'
    ) THEN
        EXECUTE 'ALTER TABLE public.calls RENAME COLUMN student_question TO incident_summary';
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'calls' AND column_name = 'student_question'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'calls' AND column_name = 'incident_summary'
    ) THEN
        EXECUTE 'UPDATE public.calls SET incident_summary = COALESCE(incident_summary, student_question)';
    END IF;

    ALTER TABLE public.calls ADD COLUMN IF NOT EXISTS incident_summary TEXT;
    ALTER TABLE public.calls ADD COLUMN IF NOT EXISTS status TEXT;
    ALTER TABLE public.calls ADD COLUMN IF NOT EXISTS script_preview TEXT;
    ALTER TABLE public.calls ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ;
END $$;

-- 4) Ensure new incident analyses table exists
CREATE TABLE IF NOT EXISTS public.incident_analyses (
    analysis_id TEXT PRIMARY KEY,
    lead_id TEXT NOT NULL,
    primary_category TEXT NOT NULL,
    severity_score INTEGER NOT NULL,
    responsible_team TEXT NOT NULL,
    analysis_json TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

-- 5) Copy legacy assessments data into incident_analyses if assessments exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'assessments'
    )
    AND EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'assessments' AND column_name = 'assessment_id'
    ) THEN
        INSERT INTO public.incident_analyses (
            analysis_id,
            lead_id,
            primary_category,
            severity_score,
            responsible_team,
            analysis_json,
            created_at
        )
        SELECT
            a.assessment_id,
            a.lead_id,
            COALESCE(a.level, 'needs_review'),
            COALESCE(a.score, 0),
            COALESCE(a.recommended_course, 'internal_review'),
            COALESCE(a.rationale, '{}'),
            a.created_at
        FROM public.assessments a
        ON CONFLICT (analysis_id) DO NOTHING;
    END IF;
END $$;

-- 6) Ensure runtime indexes expected by current backend exist
CREATE INDEX IF NOT EXISTS idx_call_transcript_turns_lead_created_at
ON public.call_transcript_turns (lead_id, created_at DESC, turn_index DESC);

CREATE INDEX IF NOT EXISTS idx_async_tasks_status_created_at
ON public.async_tasks (status, created_at ASC);

CREATE INDEX IF NOT EXISTS idx_knowledge_document_chunks_document
ON public.knowledge_document_chunks (document_id, chunk_index);

COMMIT;
