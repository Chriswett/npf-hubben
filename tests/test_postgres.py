import importlib.util
import os
import unittest

from backend.migrations import run_migrations
from backend.postgres_store import PostgresStores, _build_dsn
from backend.domain import ConflictError
from backend.security import RateLimiter
from backend.services import AuthService, PublishingService, ResponseService, SurveyService

HAS_PSYCOPG = importlib.util.find_spec("psycopg") is not None
if HAS_PSYCOPG:
    import psycopg


@unittest.skipUnless(HAS_PSYCOPG, "psycopg not installed")
class PostgresStoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.environ.get("POSTGRES_DSN") and not os.environ.get("POSTGRES_HOST"):
            raise unittest.SkipTest("Postgres not configured for tests")
        run_migrations()

    def setUp(self):
        dsn = _build_dsn()
        if HAS_PSYCOPG:
            with psycopg.connect(dsn, autocommit=True) as conn:
                conn.execute(
                    """
                    TRUNCATE users, sessions, base_profiles, network_preferences, introduction_events, mail_outbox,
                    audit_events, consent_records, pseudonyms, survey_submissions, surveys, responses, aggregations,
                    report_templates, report_versions, news_items, text_flags, redaction_events, text_reviews, ai_requests
                    RESTART IDENTITY CASCADE
                    """
                )
        self.stores = PostgresStores(dsn)
        self.auth = AuthService(self.stores.pii, RateLimiter(max_attempts=2))
        self.surveys = SurveyService(self.stores.responses)
        self.responses = ResponseService(self.stores.responses, self.stores.pii)

    def test_postgres_response_and_publish_flow(self):
        result = self.auth.register("postgres@example.com")
        user = self.auth.verify_email(result.verification_token)
        survey = self.surveys.create_survey({"questions": [{"type": "scale"}]})
        response = self.responses.submit_response(user, survey.id, {"q1": 4}, {"free": "text"})
        self.assertEqual(response.survey_id, survey.id)
        consents = self.stores.pii.list_consent_records(user_id=user.id)
        self.assertEqual(len(consents), 1)
        publishing = PublishingService(self.stores.responses)
        analyst = self.stores.pii.update_user(user.id, role="analyst")
        version = publishing.publish(analyst, template_id=1, visibility="public")
        version = publishing.set_public_url(analyst, version.id, "pg-report")
        self.assertEqual(version.published_state, "published")
        with self.assertRaises(ConflictError):
            publishing.set_public_url(analyst, version.id, "pg-report-2")


if __name__ == "__main__":
    unittest.main()
