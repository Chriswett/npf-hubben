from __future__ import annotations

import importlib.util
import os
from typing import Any, Dict, List, Optional

HAS_PSYCOPG = importlib.util.find_spec("psycopg") is not None
if HAS_PSYCOPG:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb

from .domain import (
    AggregationSnapshot,
    AiAnalysisRequest,
    AuditEvent,
    BaseProfile,
    ConsentRecord,
    IntroductionEvent,
    MailOutbox,
    NewsItem,
    NetworkPreference,
    ReportTemplate,
    ReportVersion,
    Session,
    Survey,
    SurveyResponse,
    TextFlag,
    TextRedactionEvent,
    TextReview,
    User,
    ConflictError,
)


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


class PostgresDatabase:
    def __init__(self, dsn: Optional[str] = None):
        if not HAS_PSYCOPG:
            raise RuntimeError("psycopg not installed")
        self._dsn = dsn or _build_dsn()
        self._conn = psycopg.connect(self._dsn, autocommit=True, row_factory=dict_row)

    def execute(self, query: str, params: Optional[tuple[Any, ...]] = None) -> None:
        with self._conn.cursor() as cursor:
            cursor.execute(query, params or ())

    def fetchone(self, query: str, params: Optional[tuple[Any, ...]] = None) -> Optional[Dict[str, Any]]:
        with self._conn.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()

    def fetchall(self, query: str, params: Optional[tuple[Any, ...]] = None) -> List[Dict[str, Any]]:
        with self._conn.cursor() as cursor:
            cursor.execute(query, params or ())
            return list(cursor.fetchall())


class PostgresPiiStore:
    def __init__(self, db: PostgresDatabase):
        self.db = db

    def next_id(self, name: str) -> int:
        sequence = {
            "user": "users_id_seq",
            "base_profile": "base_profiles_id_seq",
            "network_pref": "network_preferences_id_seq",
            "intro_event": "introduction_events_id_seq",
            "mail": "mail_outbox_id_seq",
            "audit": "audit_events_id_seq",
            "consent": "consent_records_id_seq",
        }.get(name, f"{name}_id_seq")
        row = self.db.fetchone("SELECT nextval(%s::regclass) AS id", (sequence,))
        return int(row["id"])

    def add_user(self, user: User) -> User:
        self.db.execute(
            "INSERT INTO users (id, email, role, verified) VALUES (%s, %s, %s, %s)",
            (user.id, user.email, user.role, user.verified),
        )
        return user

    def update_user(self, user_id: int, **updates) -> User:
        user = self.get_user(user_id)
        if user is None:
            raise ConflictError("user_not_found")
        updated = user
        for key, value in updates.items():
            updated = User(
                id=updated.id,
                email=value if key == "email" else updated.email,
                role=value if key == "role" else updated.role,
                verified=value if key == "verified" else updated.verified,
            )
        self.db.execute(
            "UPDATE users SET email=%s, role=%s, verified=%s WHERE id=%s",
            (updated.email, updated.role, updated.verified, updated.id),
        )
        return updated

    def get_user(self, user_id: int) -> Optional[User]:
        row = self.db.fetchone("SELECT id, email, role, verified FROM users WHERE id=%s", (user_id,))
        if row is None:
            return None
        return User(id=row["id"], email=row["email"], role=row["role"], verified=row["verified"])

    def get_user_by_email(self, email: str) -> Optional[User]:
        row = self.db.fetchone("SELECT id, email, role, verified FROM users WHERE email=%s", (email,))
        if row is None:
            return None
        return User(id=row["id"], email=row["email"], role=row["role"], verified=row["verified"])

    def add_session(self, session: Session) -> Session:
        self.db.execute(
            "INSERT INTO sessions (token, user_id) VALUES (%s, %s)",
            (session.token, session.user_id),
        )
        return session

    def get_session(self, token: str) -> Optional[Session]:
        row = self.db.fetchone("SELECT token, user_id FROM sessions WHERE token=%s", (token,))
        if row is None:
            return None
        return Session(token=row["token"], user_id=row["user_id"])

    def add_base_profile(self, profile: BaseProfile) -> BaseProfile:
        self.db.execute(
            "INSERT INTO base_profiles (id, user_id, kommun, categories) VALUES (%s, %s, %s, %s)",
            (profile.id, profile.user_id, profile.kommun, Jsonb(profile.categories)),
        )
        return profile

    def get_base_profile(self, user_id: int) -> Optional[BaseProfile]:
        row = self.db.fetchone(
            "SELECT id, user_id, kommun, categories FROM base_profiles WHERE user_id=%s",
            (user_id,),
        )
        if row is None:
            return None
        return BaseProfile(
            id=row["id"],
            user_id=row["user_id"],
            kommun=row["kommun"],
            categories=list(row["categories"] or []),
        )

    def list_base_profiles(self) -> List[BaseProfile]:
        rows = self.db.fetchall("SELECT id, user_id, kommun, categories FROM base_profiles")
        return [
            BaseProfile(
                id=row["id"],
                user_id=row["user_id"],
                kommun=row["kommun"],
                categories=list(row["categories"] or []),
            )
            for row in rows
        ]

    def add_network_preference(self, preference: NetworkPreference) -> NetworkPreference:
        self.db.execute(
            """
            INSERT INTO network_preferences (id, user_id, opt_in)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET opt_in=EXCLUDED.opt_in
            """,
            (preference.id, preference.user_id, preference.opt_in),
        )
        return preference

    def get_network_preference(self, user_id: int) -> Optional[NetworkPreference]:
        row = self.db.fetchone(
            "SELECT id, user_id, opt_in FROM network_preferences WHERE user_id=%s",
            (user_id,),
        )
        if row is None:
            return None
        return NetworkPreference(id=row["id"], user_id=row["user_id"], opt_in=row["opt_in"])

    def add_intro_event(self, event: IntroductionEvent) -> IntroductionEvent:
        self.db.execute(
            "INSERT INTO introduction_events (id, recipients, reason, mail_id) VALUES (%s, %s, %s, %s)",
            (event.id, Jsonb(event.recipients), event.reason, event.mail_id),
        )
        return event

    def list_intro_events(self) -> List[IntroductionEvent]:
        rows = self.db.fetchall("SELECT id, recipients, reason, mail_id FROM introduction_events")
        return [
            IntroductionEvent(
                id=row["id"],
                recipients=list(row["recipients"] or []),
                reason=row["reason"],
                mail_id=row["mail_id"],
            )
            for row in rows
        ]

    def add_outbox_mail(self, mail: MailOutbox) -> MailOutbox:
        self.db.execute(
            "INSERT INTO mail_outbox (id, recipients, subject, body) VALUES (%s, %s, %s, %s)",
            (mail.id, Jsonb(mail.recipients), mail.subject, mail.body),
        )
        return mail

    def list_outbox(self) -> List[MailOutbox]:
        rows = self.db.fetchall("SELECT id, recipients, subject, body FROM mail_outbox")
        return [
            MailOutbox(
                id=row["id"],
                recipients=list(row["recipients"] or []),
                subject=row["subject"],
                body=row["body"],
            )
            for row in rows
        ]

    def add_audit_event(self, event: AuditEvent) -> AuditEvent:
        self.db.execute(
            "INSERT INTO audit_events (id, actor_id, target_user_id, action) VALUES (%s, %s, %s, %s)",
            (event.id, event.actor_id, event.target_user_id, event.action),
        )
        return event

    def list_audit_events(self) -> List[AuditEvent]:
        rows = self.db.fetchall("SELECT id, actor_id, target_user_id, action FROM audit_events")
        return [
            AuditEvent(
                id=row["id"],
                actor_id=row["actor_id"],
                target_user_id=row["target_user_id"],
                action=row["action"],
            )
            for row in rows
        ]

    def add_consent_record(self, record: ConsentRecord) -> ConsentRecord:
        self.db.execute(
            """
            INSERT INTO consent_records (id, user_id, consent_type, version, status, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE
            SET consent_type=EXCLUDED.consent_type,
                version=EXCLUDED.version,
                status=EXCLUDED.status,
                timestamp=EXCLUDED.timestamp
            """,
            (
                record.id,
                record.user_id,
                record.consent_type,
                record.version,
                record.status,
                record.timestamp,
            ),
        )
        return record

    def list_consent_records(self, user_id: Optional[int] = None) -> List[ConsentRecord]:
        if user_id is None:
            rows = self.db.fetchall(
                "SELECT id, user_id, consent_type, version, status, timestamp FROM consent_records"
            )
        else:
            rows = self.db.fetchall(
                "SELECT id, user_id, consent_type, version, status, timestamp FROM consent_records WHERE user_id=%s",
                (user_id,),
            )
        return [
            ConsentRecord(
                id=row["id"],
                user_id=row["user_id"],
                consent_type=row["consent_type"],
                version=row["version"],
                status=row["status"],
                timestamp=row["timestamp"],
            )
            for row in rows
        ]

    def get_or_create_pseudonym(self, user_id: int) -> str:
        row = self.db.fetchone("SELECT pseudonym FROM pseudonyms WHERE user_id=%s", (user_id,))
        if row:
            return row["pseudonym"]
        pseudonym = os.urandom(8).hex()
        self.db.execute(
            "INSERT INTO pseudonyms (user_id, pseudonym) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING",
            (user_id, pseudonym),
        )
        row = self.db.fetchone("SELECT pseudonym FROM pseudonyms WHERE user_id=%s", (user_id,))
        if row is None:
            raise ConflictError("pseudonym_missing")
        return row["pseudonym"]

    def has_submitted_response(self, user_id: int, survey_id: int) -> bool:
        row = self.db.fetchone(
            "SELECT 1 FROM survey_submissions WHERE user_id=%s AND survey_id=%s",
            (user_id, survey_id),
        )
        return row is not None

    def mark_response_submitted(self, user_id: int, survey_id: int) -> None:
        self.db.execute(
            "INSERT INTO survey_submissions (user_id, survey_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (user_id, survey_id),
        )


class PostgresResponseStore:
    def __init__(self, db: PostgresDatabase):
        self.db = db

    def next_id(self, name: str) -> int:
        sequence = {
            "survey": "surveys_id_seq",
            "response": "responses_id_seq",
            "template": "report_templates_id_seq",
            "report_version": "report_versions_id_seq",
            "news": "news_items_id_seq",
            "text_flag": "text_flags_id_seq",
            "redaction_event": "redaction_events_id_seq",
            "text_review": "text_reviews_id_seq",
            "ai_request": "ai_requests_id_seq",
            "backup": "backup_id_seq",
        }.get(name, f"{name}_id_seq")
        row = self.db.fetchone("SELECT nextval(%s::regclass) AS id", (sequence,))
        return int(row["id"])

    def add_survey(self, survey: Survey) -> Survey:
        self.db.execute(
            """
            INSERT INTO surveys (id, schema, base_block_policy, feedback_mode, min_responses_default)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                survey.id,
                Jsonb(survey.schema),
                survey.base_block_policy,
                survey.feedback_mode,
                survey.min_responses_default,
            ),
        )
        return survey

    def get_survey(self, survey_id: int) -> Optional[Survey]:
        row = self.db.fetchone(
            "SELECT id, schema, base_block_policy, feedback_mode, min_responses_default FROM surveys WHERE id=%s",
            (survey_id,),
        )
        if row is None:
            return None
        return Survey(
            id=row["id"],
            schema=row["schema"],
            base_block_policy=row["base_block_policy"],
            feedback_mode=row["feedback_mode"],
            min_responses_default=row["min_responses_default"],
        )

    def list_surveys(self) -> List[Survey]:
        rows = self.db.fetchall(
            "SELECT id, schema, base_block_policy, feedback_mode, min_responses_default FROM surveys"
        )
        return [
            Survey(
                id=row["id"],
                schema=row["schema"],
                base_block_policy=row["base_block_policy"],
                feedback_mode=row["feedback_mode"],
                min_responses_default=row["min_responses_default"],
            )
            for row in rows
        ]

    def add_response(self, response: SurveyResponse) -> SurveyResponse:
        self.db.execute(
            """
            INSERT INTO responses (id, survey_id, respondent_pseudonym, answers, raw_text_fields)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                response.id,
                response.survey_id,
                response.respondent_pseudonym,
                Jsonb(response.answers),
                Jsonb(response.raw_text_fields),
            ),
        )
        return response

    def get_response_by_pseudonym_survey(self, pseudonym: str, survey_id: int) -> Optional[SurveyResponse]:
        row = self.db.fetchone(
            """
            SELECT id, survey_id, respondent_pseudonym, answers, raw_text_fields
            FROM responses WHERE respondent_pseudonym=%s AND survey_id=%s
            """,
            (pseudonym, survey_id),
        )
        if row is None:
            return None
        return SurveyResponse(
            id=row["id"],
            survey_id=row["survey_id"],
            respondent_pseudonym=row["respondent_pseudonym"],
            answers=row["answers"],
            raw_text_fields=row["raw_text_fields"] or {},
        )

    def list_responses_for_survey(self, survey_id: int) -> List[SurveyResponse]:
        rows = self.db.fetchall(
            """
            SELECT id, survey_id, respondent_pseudonym, answers, raw_text_fields
            FROM responses WHERE survey_id=%s
            """,
            (survey_id,),
        )
        return [
            SurveyResponse(
                id=row["id"],
                survey_id=row["survey_id"],
                respondent_pseudonym=row["respondent_pseudonym"],
                answers=row["answers"],
                raw_text_fields=row["raw_text_fields"] or {},
            )
            for row in rows
        ]

    def upsert_aggregation(self, snapshot: AggregationSnapshot) -> AggregationSnapshot:
        self.db.execute(
            """
            INSERT INTO aggregations (survey_id, data_version_hash, metrics, min_responses)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (survey_id) DO UPDATE
            SET data_version_hash=EXCLUDED.data_version_hash,
                metrics=EXCLUDED.metrics,
                min_responses=EXCLUDED.min_responses
            """,
            (
                snapshot.survey_id,
                snapshot.data_version_hash,
                Jsonb(snapshot.metrics),
                snapshot.min_responses,
            ),
        )
        return snapshot

    def get_aggregation(self, survey_id: int) -> Optional[AggregationSnapshot]:
        row = self.db.fetchone(
            "SELECT survey_id, data_version_hash, metrics, min_responses FROM aggregations WHERE survey_id=%s",
            (survey_id,),
        )
        if row is None:
            return None
        return AggregationSnapshot(
            survey_id=row["survey_id"],
            data_version_hash=row["data_version_hash"],
            metrics=row["metrics"],
            min_responses=row["min_responses"],
        )

    def add_report_template(self, template: ReportTemplate) -> ReportTemplate:
        self.db.execute(
            "INSERT INTO report_templates (id, survey_id, blocks) VALUES (%s, %s, %s)",
            (template.id, template.survey_id, Jsonb(template.blocks)),
        )
        return template

    def get_report_template(self, template_id: int) -> Optional[ReportTemplate]:
        row = self.db.fetchone(
            "SELECT id, survey_id, blocks FROM report_templates WHERE id=%s",
            (template_id,),
        )
        if row is None:
            return None
        return ReportTemplate(id=row["id"], survey_id=row["survey_id"], blocks=row["blocks"])

    def add_report_version(self, version: ReportVersion) -> ReportVersion:
        self.db.execute(
            """
            INSERT INTO report_versions (id, template_id, visibility, published_state, canonical_url, replaced_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                version.id,
                version.template_id,
                version.visibility,
                version.published_state,
                version.canonical_url,
                version.replaced_by,
            ),
        )
        return version

    def update_report_version(self, version_id: int, **updates) -> ReportVersion:
        version = self.get_report_version(version_id)
        if version is None:
            raise ConflictError("report_version_not_found")
        if version.published_state == "published":
            allowed = {"replaced_by"}
            if set(updates.keys()) - allowed:
                raise ConflictError("report_version_immutable")
        updated = ReportVersion(
            id=version.id,
            template_id=updates.get("template_id", version.template_id),
            visibility=updates.get("visibility", version.visibility),
            published_state=updates.get("published_state", version.published_state),
            canonical_url=updates.get("canonical_url", version.canonical_url),
            replaced_by=updates.get("replaced_by", version.replaced_by),
        )
        self.db.execute(
            """
            UPDATE report_versions
            SET template_id=%s,
                visibility=%s,
                published_state=%s,
                canonical_url=%s,
                replaced_by=%s
            WHERE id=%s
            """,
            (
                updated.template_id,
                updated.visibility,
                updated.published_state,
                updated.canonical_url,
                updated.replaced_by,
                updated.id,
            ),
        )
        return updated

    def get_report_version(self, version_id: int) -> Optional[ReportVersion]:
        row = self.db.fetchone(
            """
            SELECT id, template_id, visibility, published_state, canonical_url, replaced_by
            FROM report_versions WHERE id=%s
            """,
            (version_id,),
        )
        if row is None:
            return None
        return ReportVersion(
            id=row["id"],
            template_id=row["template_id"],
            visibility=row["visibility"],
            published_state=row["published_state"],
            canonical_url=row["canonical_url"],
            replaced_by=row["replaced_by"],
        )

    def get_report_version_by_url(self, url: str) -> Optional[ReportVersion]:
        row = self.db.fetchone(
            """
            SELECT id, template_id, visibility, published_state, canonical_url, replaced_by
            FROM report_versions WHERE canonical_url=%s
            """,
            (url,),
        )
        if row is None:
            return None
        return ReportVersion(
            id=row["id"],
            template_id=row["template_id"],
            visibility=row["visibility"],
            published_state=row["published_state"],
            canonical_url=row["canonical_url"],
            replaced_by=row["replaced_by"],
        )

    def list_report_versions(self) -> List[ReportVersion]:
        rows = self.db.fetchall(
            "SELECT id, template_id, visibility, published_state, canonical_url, replaced_by FROM report_versions"
        )
        return [
            ReportVersion(
                id=row["id"],
                template_id=row["template_id"],
                visibility=row["visibility"],
                published_state=row["published_state"],
                canonical_url=row["canonical_url"],
                replaced_by=row["replaced_by"],
            )
            for row in rows
        ]

    def add_news_item(self, item: NewsItem) -> NewsItem:
        self.db.execute("INSERT INTO news_items (id, title, body) VALUES (%s, %s, %s)", (item.id, item.title, item.body))
        return item

    def list_news(self) -> List[NewsItem]:
        rows = self.db.fetchall("SELECT id, title, body FROM news_items")
        return [NewsItem(id=row["id"], title=row["title"], body=row["body"]) for row in rows]

    def add_text_flag(self, flag: TextFlag) -> TextFlag:
        self.db.execute(
            "INSERT INTO text_flags (id, response_id, reason) VALUES (%s, %s, %s)",
            (flag.id, flag.response_id, flag.reason),
        )
        return flag

    def add_redaction_event(self, event: TextRedactionEvent) -> TextRedactionEvent:
        self.db.execute(
            "INSERT INTO redaction_events (id, flag_id, curator_id, note) VALUES (%s, %s, %s, %s)",
            (event.id, event.flag_id, event.curator_id, event.note),
        )
        return event

    def list_text_flags(self) -> List[TextFlag]:
        rows = self.db.fetchall("SELECT id, response_id, reason FROM text_flags")
        return [TextFlag(id=row["id"], response_id=row["response_id"], reason=row["reason"]) for row in rows]

    def list_redaction_events(self) -> List[TextRedactionEvent]:
        rows = self.db.fetchall("SELECT id, flag_id, curator_id, note FROM redaction_events")
        return [
            TextRedactionEvent(id=row["id"], flag_id=row["flag_id"], curator_id=row["curator_id"], note=row["note"])
            for row in rows
        ]

    def add_text_review(self, review: TextReview) -> TextReview:
        self.db.execute(
            """
            INSERT INTO text_reviews (id, response_id, status, flagged_for_review, reviewed_by, reviewed_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                review.id,
                review.response_id,
                review.status,
                review.flagged_for_review,
                review.reviewed_by,
                review.reviewed_at,
            ),
        )
        return review

    def update_text_review(self, review_id: int, **updates) -> TextReview:
        review = self.get_text_review(review_id)
        if review is None:
            raise ConflictError("text_review_not_found")
        updated = TextReview(
            id=review.id,
            response_id=review.response_id,
            status=updates.get("status", review.status),
            flagged_for_review=updates.get("flagged_for_review", review.flagged_for_review),
            reviewed_by=updates.get("reviewed_by", review.reviewed_by),
            reviewed_at=updates.get("reviewed_at", review.reviewed_at),
        )
        self.db.execute(
            """
            UPDATE text_reviews
            SET status=%s, flagged_for_review=%s, reviewed_by=%s, reviewed_at=%s
            WHERE id=%s
            """,
            (
                updated.status,
                updated.flagged_for_review,
                updated.reviewed_by,
                updated.reviewed_at,
                updated.id,
            ),
        )
        return updated

    def get_text_review(self, review_id: int) -> Optional[TextReview]:
        row = self.db.fetchone(
            """
            SELECT id, response_id, status, flagged_for_review, reviewed_by, reviewed_at
            FROM text_reviews WHERE id=%s
            """,
            (review_id,),
        )
        if row is None:
            return None
        return TextReview(
            id=row["id"],
            response_id=row["response_id"],
            status=row["status"],
            flagged_for_review=row["flagged_for_review"],
            reviewed_by=row["reviewed_by"],
            reviewed_at=row["reviewed_at"],
        )

    def get_text_review_for_response(self, response_id: int) -> Optional[TextReview]:
        row = self.db.fetchone(
            """
            SELECT id, response_id, status, flagged_for_review, reviewed_by, reviewed_at
            FROM text_reviews WHERE response_id=%s
            """,
            (response_id,),
        )
        if row is None:
            return None
        return TextReview(
            id=row["id"],
            response_id=row["response_id"],
            status=row["status"],
            flagged_for_review=row["flagged_for_review"],
            reviewed_by=row["reviewed_by"],
            reviewed_at=row["reviewed_at"],
        )

    def list_text_reviews(self) -> List[TextReview]:
        rows = self.db.fetchall(
            "SELECT id, response_id, status, flagged_for_review, reviewed_by, reviewed_at FROM text_reviews"
        )
        return [
            TextReview(
                id=row["id"],
                response_id=row["response_id"],
                status=row["status"],
                flagged_for_review=row["flagged_for_review"],
                reviewed_by=row["reviewed_by"],
                reviewed_at=row["reviewed_at"],
            )
            for row in rows
        ]

    def list_public_texts(self, allowed_statuses: List[str]) -> List[str]:
        rows = self.db.fetchall(
            """
            SELECT responses.raw_text_fields
            FROM text_reviews
            JOIN responses ON responses.id = text_reviews.response_id
            WHERE text_reviews.status = ANY(%s)
            """,
            (allowed_statuses,),
        )
        texts: List[str] = []
        for row in rows:
            raw_fields = row["raw_text_fields"] or {}
            texts.extend(list(raw_fields.values()))
        return texts

    def add_ai_request(self, request: AiAnalysisRequest) -> AiAnalysisRequest:
        self.db.execute(
            "INSERT INTO ai_requests (id, prompt) VALUES (%s, %s)",
            (request.id, request.prompt),
        )
        return request

    def list_ai_requests(self) -> List[AiAnalysisRequest]:
        rows = self.db.fetchall("SELECT id, prompt FROM ai_requests")
        return [AiAnalysisRequest(id=row["id"], prompt=row["prompt"]) for row in rows]


class PostgresStores:
    def __init__(self, dsn: Optional[str] = None):
        db = PostgresDatabase(dsn)
        self.pii = PostgresPiiStore(db)
        self.responses = PostgresResponseStore(db)
