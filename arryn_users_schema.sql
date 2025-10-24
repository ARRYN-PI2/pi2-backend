-- =============================================================================
-- ARRYN USERS MODULE (manual DDL)  —  crea SOLO tablas del módulo, no las core de Django
-- Esquema: public
-- IMPORTANTE: después ejecuta `python manage.py migrate --fake-initial`
-- =============================================================================

SET search_path = public;

-- UUID helper
DO $$
BEGIN
  BEGIN
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
  EXCEPTION WHEN insufficient_privilege THEN
    -- continuar si no hay permisos (en RDS usa rds_superuser)
    NULL;
  END;

  IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname='uuid_generate_v4') THEN
    EXECUTE $F$
      CREATE OR REPLACE FUNCTION uuid_generate_v4()
      RETURNS uuid LANGUAGE SQL AS $$ SELECT gen_random_uuid() $$;
    $F$;
  END IF;
END$$;

-- 1) api_role  (equivale a tu modelo Role)
CREATE TABLE IF NOT EXISTS public.api_role (
  level        SMALLINT PRIMARY KEY CHECK (level BETWEEN 1 AND 4),
  name         VARCHAR(50)  NOT NULL UNIQUE,
  description  TEXT         NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_api_role_name ON public.api_role(name);

-- Seed 1..4
INSERT INTO public.api_role (level, name, description) VALUES
 (1,'Guest','Visitante sin sesión'),
 (2,'User','Usuario autenticado estándar'),
 (3,'Editor','Puede editar productos/ítems (no usuarios)'),
 (4,'Admin','Administración total (usuarios y productos'))
ON CONFLICT (level) DO UPDATE
SET name=EXCLUDED.name, description=EXCLUDED.description;

-- 2) api_user  (equivale a tu modelo User que hereda AbstractUser)
-- Nota: Django crea varias columnas y tablas M2M (groups, permissions) en migraciones.
-- Aquí creamos un esqueleto compatible con el CreateModel de tu 0001.
CREATE TABLE IF NOT EXISTS public.api_user (
  id              BIGSERIAL PRIMARY KEY,
  password        VARCHAR(128) NOT NULL,
  last_login      TIMESTAMPTZ,
  is_superuser    BOOLEAN NOT NULL DEFAULT FALSE,

  username        VARCHAR(150) NOT NULL UNIQUE,
  first_name      VARCHAR(150) NOT NULL DEFAULT '',
  last_name       VARCHAR(150) NOT NULL DEFAULT '',
  email           VARCHAR(254) NOT NULL UNIQUE,

  is_staff        BOOLEAN NOT NULL DEFAULT FALSE,
  is_active       BOOLEAN NOT NULL DEFAULT TRUE,
  date_joined     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

  -- FK al rol
  role_id         SMALLINT NOT NULL DEFAULT 2
                  REFERENCES public.api_role(level) ON UPDATE CASCADE,

  -- índices útiles
  CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$')
);
CREATE INDEX IF NOT EXISTS idx_api_user_role_id  ON public.api_user(role_id);
CREATE INDEX IF NOT EXISTS idx_api_user_email    ON public.api_user(email);

-- 2.1) M2M que Django crea para permisos/grupos (nombres por convención)
-- Estos nombres deben calzar con tus migraciones de User (revisa 0001).
CREATE TABLE IF NOT EXISTS public.api_user_groups (
  id        BIGSERIAL PRIMARY KEY,
  user_id   BIGINT NOT NULL REFERENCES public.api_user(id) ON DELETE CASCADE,
  group_id  INTEGER NOT NULL REFERENCES public.auth_group(id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS api_user_groups_user_group_uniq
  ON public.api_user_groups(user_id, group_id);

CREATE TABLE IF NOT EXISTS public.api_user_user_permissions (
  id              BIGSERIAL PRIMARY KEY,
  user_id         BIGINT NOT NULL REFERENCES public.api_user(id) ON DELETE CASCADE,
  permission_id   INTEGER NOT NULL REFERENCES public.auth_permission(id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS api_user_user_permissions_uniq
  ON public.api_user_user_permissions(user_id, permission_id);

-- OJO: las tablas auth_group y auth_permission las crean las migraciones core de Django.
-- Por eso, ejecuta `python manage.py migrate --fake-initial` después de este script.

-- 3) user_sessions (opcional si guardarás sesiones JWT del lado servidor)
CREATE TABLE IF NOT EXISTS public.user_sessions (
  session_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id        BIGINT NOT NULL REFERENCES public.api_user(id) ON DELETE CASCADE,
  jwt_token_hash VARCHAR(255) NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_activity  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at     TIMESTAMPTZ NOT NULL,
  is_active      BOOLEAN NOT NULL DEFAULT TRUE,
  ip_address     INET,
  user_agent     TEXT,
  device_info    JSONB,
  CONSTRAINT chk_expires_future CHECK (expires_at > created_at)
);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id    ON public.user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_tok_hash   ON public.user_sessions(jwt_token_hash);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active     ON public.user_sessions(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON public.user_sessions(expires_at);

-- trigger para last_activity
CREATE OR REPLACE FUNCTION public.touch_last_activity()
RETURNS TRIGGER AS $$
BEGIN
  NEW.last_activity = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_user_sessions_touch ON public.user_sessions;
CREATE TRIGGER trg_user_sessions_touch
BEFORE UPDATE ON public.user_sessions
FOR EACH ROW
WHEN (OLD.is_active = TRUE)
EXECUTE FUNCTION public.touch_last_activity();

-- 4) user_notifications (si lo usas)
CREATE TABLE IF NOT EXISTS public.user_notifications (
  notification_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id         BIGINT NOT NULL REFERENCES public.api_user(id) ON DELETE CASCADE,
  type            VARCHAR(50)  NOT NULL,
  title           VARCHAR(255) NOT NULL,
  message         TEXT         NOT NULL,
  data            JSONB,
  is_read         BOOLEAN NOT NULL DEFAULT FALSE,
  priority        VARCHAR(20) NOT NULL DEFAULT 'normal' CHECK (priority IN ('low','normal','high','urgent')),
  expires_at      TIMESTAMPTZ,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  read_at         TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_user_notifications_user_id  ON public.user_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_user_notifications_unread   ON public.user_notifications(user_id, is_read, created_at) WHERE is_read = FALSE;
CREATE INDEX IF NOT EXISTS idx_user_notifications_type     ON public.user_notifications(type);
CREATE INDEX IF NOT EXISTS idx_user_notifications_priority ON public.user_notifications(user_id, priority, created_at);

-- Verificación amistosa
DO $$
BEGIN
  RAISE NOTICE 'Creación manual de tablas del módulo completada (api_role, api_user, m2m, user_sessions, user_notifications). Recuerda ejecutar: python manage.py migrate --fake-initial';
END$$;