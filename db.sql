 -- -------------------------------------------------
  -- 1. Core tables
  -- -------------------------------------------------

  -- Users (individual accounts; belong to a team)
  CREATE TABLE public.users (
      id            UUID      PRIMARY KEY DEFAULT gen_random_uuid(),
      email         TEXT      NOT NULL UNIQUE,
      password_hash TEXT      NOT NULL,
      full_name     TEXT,
      is_active     BOOLEAN   NOT NULL DEFAULT TRUE,
      is_admin      BOOLEAN   NOT NULL DEFAULT FALSE,
      created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
  );

  -- Teams (one team per competition entry)
  CREATE TABLE public.teams (
      id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      name         TEXT NOT NULL UNIQUE,
      display_name TEXT,
      created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
  );

  -- Junction table linking users ↔ teams (many‑to‑many, but most use‑cases are one‑to‑many)
  CREATE TABLE public.team_members (
      team_id UUID REFERENCES public.teams(id) ON DELETE CASCADE,
      user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
      role    TEXT CHECK (role IN ('owner','member')) NOT NULL DEFAULT 'member',
      PRIMARY KEY (team_id, user_id)
  );

  -- Challenge definitions (static metadata, same for every team)
  CREATE TABLE public.challenges (
      id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      slug         TEXT NOT NULL UNIQUE,          -- e.g. "sql-injection"
      title        TEXT NOT NULL,
      category     TEXT NOT NULL,                 -- e.g. "Web"
      difficulty   TEXT CHECK (difficulty IN ('Easy','Medium','Hard','Extreme')) NOT NULL,
      description  TEXT NOT NULL,                -- markdown shown on challenge page
      hints        TEXT[],                       -- array of markdown hints
      flag_type    TEXT CHECK (flag_type IN ('static','dynamic')) NOT NULL DEFAULT 'dynamic',
      points_base  INTEGER NOT NULL DEFAULT 500, -- base points (may decay)
      created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
      updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
  );

  -- Per‑team solves (each solve is a row; unique per team+challenge)
  CREATE TABLE public.solves (
      id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      team_id      UUID REFERENCES public.teams(id) ON DELETE CASCADE,
      challenge_id UUID REFERENCES public.challenges(id) ON DELETE CASCADE,
      flag_submitted TEXT NOT NULL,
      is_correct   BOOLEAN NOT NULL,
      solved_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
      points_awarded INTEGER,
      UNIQUE (team_id, challenge_id)
  );

  -- -------------------------------------------------
  -- 2. Admin / audit tables
  -- -------------------------------------------------

  -- Audit log for privileged actions (admin UI)
  CREATE TABLE public.audit_logs (
      id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      actor_user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
      action       TEXT NOT NULL,
      target_type  TEXT,            -- e.g. "challenge", "team"
      target_id    UUID,
      details      JSONB,
      ip_address   INET,
      created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
  );

  -- Scoreboard view (materialised for fast read)
  CREATE MATERIALIZED VIEW public.team_scoreboard AS
  SELECT
      t.id          AS team_id,
      t.display_name,
      COALESCE(SUM(s.points_awarded),0) AS total_points,
      COUNT(s.id)   AS solves_count,
      MAX(s.solved_at) AS last_solve_at
  FROM public.teams t
  LEFT JOIN public.solves s ON s.team_id = t.id
  GROUP BY t.id, t.display_name
  WITH DATA;

  -- Refresh policy (run every minute via a cronjob)
  CREATE OR REPLACE FUNCTION public.refresh_scoreboard()
  RETURNS void LANGUAGE plpgsql AS $$
  BEGIN
      REFRESH MATERIALIZED VIEW CONCURRENTLY public.team_scoreboard;
  END;
  $$;

  -- -------------------------------------------------
  -- 3. Row‑Level Security (RLS)
  -- -------------------------------------------------
  ALTER TABLE public.solves ENABLE ROW LEVEL SECURITY;
  CREATE POLICY solves_team_isolation ON public.solves
      USING (team_id = current_setting('app.current_team_id')::uuid);

  ALTER TABLE public.team_members ENABLE ROW LEVEL SECURITY;
  CREATE POLICY team_members_isolation ON public.team_members
      USING (team_id = current_setting('app.current_team_id')::uuid);

  -- Helper function to set the current team id (called by FastAPI middleware)
  CREATE OR REPLACE FUNCTION public.set_current_team(tid UUID)
  RETURNS void LANGUAGE plpgsql AS $$
  BEGIN
      PERFORM set_config('app.current_team_id', tid::text, true);
  END;
  $$;
