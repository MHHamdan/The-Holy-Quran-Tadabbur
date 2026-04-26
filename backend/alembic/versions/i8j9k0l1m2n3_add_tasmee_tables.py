"""Add Tasmee tables

Revision ID: i8j9k0l1m2n3
Revises: h7i8j9k0l1m2
Create Date: 2025-01-22

Pure-SQL implementation so that SQLAlchemy's _on_table_create event never
fires a redundant CREATE TYPE after we have already created the types via the
idempotent DO/EXCEPTION block.  CREATE TABLE/INDEX IF NOT EXISTS make every
statement safe to re-run after a partial failure.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'i8j9k0l1m2n3'
down_revision: Union[str, None] = 'h7i8j9k0l1m2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enum types (idempotent — safe on re-run) ──────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE session_status AS ENUM ('active','completed','paused','cancelled');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE mistake_type AS ENUM (
                'substitution','deletion','insertion',
                'repetition','hesitation','mispronunciation');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE event_type AS ENUM (
                'session_start','session_end','session_pause','session_resume',
                'word_matched','mistake_detected','correction','verse_completed');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # ── Tables (IF NOT EXISTS — idempotent) ───────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS tasmee_sessions (
            id                       SERIAL PRIMARY KEY,
            user_id                  VARCHAR(255),
            device_id                VARCHAR(255),
            status                   session_status NOT NULL DEFAULT 'active',
            created_at               TIMESTAMP NOT NULL DEFAULT now(),
            updated_at               TIMESTAMP NOT NULL DEFAULT now(),
            completed_at             TIMESTAMP,
            sura_no                  INTEGER NOT NULL,
            sura_name_ar             VARCHAR(100),
            sura_name_en             VARCHAR(100),
            aya_start                INTEGER NOT NULL,
            aya_end                  INTEGER NOT NULL,
            total_verses             INTEGER NOT NULL DEFAULT 0,
            total_words              INTEGER NOT NULL DEFAULT 0,
            audio_file_path          VARCHAR(500),
            audio_duration_seconds   FLOAT,
            audio_format             VARCHAR(50),
            words_completed          INTEGER NOT NULL DEFAULT 0,
            words_correct            INTEGER NOT NULL DEFAULT 0,
            mistakes_count           INTEGER NOT NULL DEFAULT 0,
            accuracy_score           FLOAT,
            completion_percentage    FLOAT NOT NULL DEFAULT 0,
            active_duration_seconds  FLOAT NOT NULL DEFAULT 0,
            total_duration_seconds   FLOAT,
            stt_provider             VARCHAR(50) DEFAULT 'faster-whisper',
            stt_model                VARCHAR(50) DEFAULT 'base',
            metadata                 JSON
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasmee_sessions_user_id ON tasmee_sessions (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasmee_sessions_status  ON tasmee_sessions (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasmee_sessions_sura_no ON tasmee_sessions (sura_no)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS tasmee_events (
            id                   SERIAL PRIMARY KEY,
            session_id           INTEGER NOT NULL
                                     REFERENCES tasmee_sessions(id) ON DELETE CASCADE,
            event_type           event_type NOT NULL,
            timestamp            FLOAT NOT NULL,
            expected_word_index  INTEGER,
            recognized_word      VARCHAR(100),
            confidence           FLOAT,
            data                 JSON,
            created_at           TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasmee_events_session_id ON tasmee_events (session_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS tasmee_mistakes (
            id                   SERIAL PRIMARY KEY,
            session_id           INTEGER NOT NULL
                                     REFERENCES tasmee_sessions(id) ON DELETE CASCADE,
            mistake_type         mistake_type NOT NULL,
            severity             VARCHAR(20) NOT NULL DEFAULT 'moderate',
            word_position        INTEGER NOT NULL,
            verse_sura_no        INTEGER,
            verse_aya_no         INTEGER,
            expected_word        VARCHAR(100) NOT NULL,
            expected_normalized  VARCHAR(100),
            actual_word          VARCHAR(100),
            actual_normalized    VARCHAR(100),
            timestamp            FLOAT NOT NULL,
            confidence           FLOAT,
            context_before       JSON,
            context_after        JSON,
            was_corrected        BOOLEAN NOT NULL DEFAULT false,
            correction_timestamp FLOAT,
            created_at           TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasmee_mistakes_session_id   ON tasmee_mistakes (session_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasmee_mistakes_mistake_type ON tasmee_mistakes (mistake_type)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS tasmee_progress (
            id                   SERIAL PRIMARY KEY,
            user_id              VARCHAR(255),
            device_id            VARCHAR(255),
            sura_no              INTEGER NOT NULL,
            aya_no               INTEGER NOT NULL,
            total_attempts       INTEGER NOT NULL DEFAULT 0,
            successful_attempts  INTEGER NOT NULL DEFAULT 0,
            best_accuracy        FLOAT,
            average_accuracy     FLOAT,
            is_memorized         BOOLEAN NOT NULL DEFAULT false,
            memorized_at         TIMESTAMP,
            last_practiced_at    TIMESTAMP,
            created_at           TIMESTAMP NOT NULL DEFAULT now(),
            updated_at           TIMESTAMP NOT NULL DEFAULT now(),
            CONSTRAINT uq_tasmee_progress_user_verse
                UNIQUE (user_id, device_id, sura_no, aya_no)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasmee_progress_user_id  ON tasmee_progress (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tasmee_progress_sura_aya ON tasmee_progress (sura_no, aya_no)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tasmee_progress")
    op.execute("DROP TABLE IF EXISTS tasmee_mistakes")
    op.execute("DROP TABLE IF EXISTS tasmee_events")
    op.execute("DROP TABLE IF EXISTS tasmee_sessions")
    op.execute("DROP TYPE IF EXISTS event_type")
    op.execute("DROP TYPE IF EXISTS mistake_type")
    op.execute("DROP TYPE IF EXISTS session_status")
