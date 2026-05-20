from collections.abc import Generator

import psycopg
from pgvector.psycopg import register_vector

from app.settings import get_database_url, get_embedding_dimensions


def get_connection() -> psycopg.Connection:
    """Open a new PostgreSQL connection with pgvector types registered."""
    conn = psycopg.connect(get_database_url(), autocommit=False)
    register_vector(conn)
    return conn


def connection_ctx() -> Generator[psycopg.Connection, None, None]:
    """Yield a connection for callers that manage transactions manually."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def ensure_document_chunks_table(conn: psycopg.Connection) -> None:
    """Create document_chunks if missing (for DB volumes created before this table existed)."""
    dim = get_embedding_dimensions()
    sql = f"""
    CREATE TABLE IF NOT EXISTS document_chunks (
        id BIGSERIAL PRIMARY KEY,
        source_path TEXT NOT NULL,
        chunk_index INT NOT NULL,
        content TEXT NOT NULL,
        embedding vector({dim}) NOT NULL,
        created_at TIMESTAMPTZ DEFAULT now(),
        UNIQUE (source_path, chunk_index)
    );
    """
    conn.execute(sql)


def ensure_users_table(conn: psycopg.Connection) -> None:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id            SERIAL PRIMARY KEY,
        email         TEXT NOT NULL UNIQUE,
        name          TEXT,
        password_hash TEXT NOT NULL,
        role          TEXT NOT NULL CHECK (role IN ('admin', 'staff')),
        created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        deleted_at    TIMESTAMPTZ
    )
    """)


def ensure_chat_logs_table(conn: psycopg.Connection) -> None:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS chat_logs (
        id                SERIAL PRIMARY KEY,
        session_id        UUID NOT NULL,
        user_id           INT REFERENCES users(id) ON DELETE SET NULL,
        timestamp         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        prompt_tokens     INT NOT NULL,
        completion_tokens INT NOT NULL,
        latency_ms        INT NOT NULL,
        model             TEXT NOT NULL,
        cost_eur          NUMERIC(10, 6) NOT NULL,
        origin            TEXT
    )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_logs_timestamp  ON chat_logs (timestamp)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_logs_session_id ON chat_logs (session_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_logs_user_id    ON chat_logs (user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_logs_origin     ON chat_logs (origin)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_logs_ts_model   ON chat_logs (timestamp, model)")


def ensure_chat_logs_columns(conn: psycopg.Connection) -> None:
    """Idempotently migrate chat_logs columns after the initial schema."""
    conn.execute("ALTER TABLE chat_logs ADD COLUMN IF NOT EXISTS retrieved_sources TEXT[]")
    conn.execute("ALTER TABLE chat_logs DROP COLUMN IF EXISTS duration_ms")


def ensure_admin_audit_log_table(conn: psycopg.Connection) -> None:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS admin_audit_log (
        id             SERIAL PRIMARY KEY,
        actor_user_id  INT NOT NULL REFERENCES users(id),
        action         TEXT NOT NULL,
        target_user_id INT REFERENCES users(id) ON DELETE SET NULL,
        metadata       JSONB,
        timestamp      TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """)


def ensure_schema_at_startup() -> None:
    """Apply idempotent DDL before serving traffic."""
    with get_connection() as conn:
        ensure_document_chunks_table(conn)
        ensure_users_table(conn)
        ensure_chat_logs_table(conn)
        ensure_chat_logs_columns(conn)
        ensure_admin_audit_log_table(conn)
        conn.commit()


