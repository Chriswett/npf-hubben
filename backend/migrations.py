from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import psycopg


def _build_dsn() -> str:
    dsn = os.environ.get("POSTGRES_DSN")
    if dsn:
        return dsn
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    database = os.environ.get("POSTGRES_DB", "postgres")
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def _apply_migrations(conn: "psycopg.Connection") -> None:
    statements = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            role TEXT NOT NULL,
            verified BOOLEAN NOT NULL DEFAULT FALSE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS base_profiles (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,
            kommun TEXT NOT NULL,
            categories JSONB NOT NULL DEFAULT '[]'::jsonb
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS network_preferences (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL,
            opt_in BOOLEAN NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS introduction_events (
            id SERIAL PRIMARY KEY,
            recipients JSONB NOT NULL DEFAULT '[]'::jsonb,
            reason TEXT NOT NULL,
            mail_id INTEGER
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS mail_outbox (
            id SERIAL PRIMARY KEY,
            recipients JSONB NOT NULL DEFAULT '[]'::jsonb,
            subject TEXT NOT NULL,
            body TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS audit_events (
            id SERIAL PRIMARY KEY,
            actor_id INTEGER NOT NULL,
            target_user_id INTEGER,
            action TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS consent_records (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            consent_type TEXT NOT NULL,
            version TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS pseudonyms (
            user_id INTEGER PRIMARY KEY,
            pseudonym TEXT UNIQUE NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS survey_submissions (
            user_id INTEGER NOT NULL,
            survey_id INTEGER NOT NULL,
            PRIMARY KEY (user_id, survey_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS surveys (
            id SERIAL PRIMARY KEY,
            schema JSONB NOT NULL,
            base_block_policy TEXT NOT NULL,
            feedback_mode TEXT NOT NULL,
            min_responses_default INTEGER NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS responses (
            id SERIAL PRIMARY KEY,
            survey_id INTEGER NOT NULL,
            respondent_pseudonym TEXT NOT NULL,
            answers JSONB NOT NULL,
            raw_text_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
            UNIQUE (respondent_pseudonym, survey_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS aggregations (
            survey_id INTEGER PRIMARY KEY,
            data_version_hash TEXT NOT NULL,
            metrics JSONB NOT NULL,
            min_responses INTEGER NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS report_templates (
            id SERIAL PRIMARY KEY,
            survey_id INTEGER NOT NULL,
            blocks JSONB NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS report_versions (
            id SERIAL PRIMARY KEY,
            template_id INTEGER NOT NULL,
            visibility TEXT NOT NULL,
            published_state TEXT NOT NULL,
            canonical_url TEXT UNIQUE,
            replaced_by INTEGER
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS news_items (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            body TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS text_flags (
            id SERIAL PRIMARY KEY,
            response_id INTEGER NOT NULL,
            reason TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS redaction_events (
            id SERIAL PRIMARY KEY,
            flag_id INTEGER NOT NULL,
            curator_id INTEGER NOT NULL,
            note TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS text_reviews (
            id SERIAL PRIMARY KEY,
            response_id INTEGER UNIQUE NOT NULL,
            status TEXT NOT NULL,
            flagged_for_review BOOLEAN NOT NULL DEFAULT FALSE,
            reviewed_by INTEGER,
            reviewed_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS ai_requests (
            id SERIAL PRIMARY KEY,
            prompt TEXT NOT NULL
        )
        """,
        "CREATE SEQUENCE IF NOT EXISTS backup_id_seq",
    ]
    with conn.cursor() as cursor:
        for statement in statements:
            cursor.execute(statement)


def run_migrations() -> None:
    import psycopg

    dsn = _build_dsn()
    with psycopg.connect(dsn, autocommit=True) as conn:
        _apply_migrations(conn)


if __name__ == "__main__":
    run_migrations()
