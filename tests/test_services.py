import json
import unittest

from backend.domain import ConflictError, RateLimitError, UnauthorizedError, ValidationError
from backend.logging import sanitize_log
from backend.security import RateLimiter, require_role
from backend.services import (
    AdminService,
    AggregationService,
    AiService,
    AuthService,
    BackupService,
    BaseProfileService,
    NetworkService,
    PublishingService,
    PublicSiteService,
    ReportService,
    ResponseService,
    SurveyService,
    ModerationService,
    SurveyFlowService,
)
from backend.storage import InMemoryStores


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.stores = InMemoryStores()
        self.rate_limiter = RateLimiter(max_attempts=1)
        self.auth = AuthService(self.stores.pii, self.rate_limiter)
        self.surveys = SurveyService(self.stores.responses)
        self.responses = ResponseService(self.stores.responses)
        self.aggregations = AggregationService(self.stores.responses)
        self.reports = ReportService(self.stores.responses)
        self.network = NetworkService(self.stores.pii)
        self.ai = AiService(self.stores.responses)
        self.backup = BackupService(self.stores.responses)
        self.admin = AdminService(self.stores.pii)
        self.survey_flow = SurveyFlowService(self.stores.pii, self.stores.responses)
        self.public_site = PublicSiteService(self.stores.responses, self.stores.pii)

    def test_us01_registration_and_verification(self):
        result = self.auth.register("parent@example.com")
        self.assertFalse(result.user.verified)
        verified_user = self.auth.verify_email(result.verification_token)
        self.assertTrue(verified_user.verified)
        session = self.auth.login("parent@example.com")
        self.assertEqual(session.user_id, verified_user.id)

    def test_us01_unverified_cannot_submit_response(self):
        result = self.auth.register("parent2@example.com")
        survey = self.surveys.create_survey({"questions": [{"type": "scale"}]})
        with self.assertRaises(ValidationError):
            self.responses.submit_response(result.user, survey.id, {"q1": 3})
        start_state = self.survey_flow.start_survey(result.user, survey.id)
        self.assertTrue(start_state["needs_base_block"])

    def test_us02_public_payload_has_no_pii(self):
        survey = self.surveys.create_survey({"questions": [{"type": "scale"}]})
        template = self.reports.create_template(survey.id, [{"type": "text", "content": "Hej $kommun"}])
        snapshot = self.aggregations.build_snapshot(survey.id, min_responses=2)
        payload = self.reports.build_report_payload(template, snapshot, kommun="Test")
        self.assertNotIn("email", json.dumps(payload))

    def test_us02_response_store_has_no_pii(self):
        result = self.auth.register("parent3@example.com")
        user = self.auth.verify_email(result.verification_token)
        survey = self.surveys.create_survey({"questions": [{"type": "scale"}]})
        response = self.responses.submit_response(user, survey.id, {"q1": 2})
        self.assertFalse(hasattr(response, "email"))

    def test_us03_schema_validation_and_defaults(self):
        with self.assertRaises(ValidationError):
            self.surveys.validate_schema({"questions": [{"type": "unsupported"}]})
        survey = self.surveys.create_survey({"questions": [{"type": "scale"}]})
        self.assertEqual(survey.base_block_policy, "enabled")
        self.assertEqual(survey.feedback_mode, "section")

    def test_us04_base_profile_only_once(self):
        result = self.auth.register("parent4@example.com")
        user = self.auth.verify_email(result.verification_token)
        base_service = BaseProfileService(self.stores.pii)
        profile = base_service.ensure_base_profile(user, "Kommun A", ["kategori"])
        profile_again = base_service.ensure_base_profile(user, "Kommun B", ["annan"])
        self.assertEqual(profile.id, profile_again.id)
        self.assertEqual(profile_again.kommun, "Kommun A")
        survey = self.surveys.create_survey({"questions": [{"type": "scale"}]})
        start_state = self.survey_flow.start_survey(user, survey.id)
        self.assertFalse(start_state["needs_base_block"])

    def test_us05_duplicate_response_blocked(self):
        result = self.auth.register("parent5@example.com")
        user = self.auth.verify_email(result.verification_token)
        survey = self.surveys.create_survey({"questions": [{"type": "scale"}]})
        self.responses.submit_response(user, survey.id, {"q1": 1})
        with self.assertRaises(ConflictError):
            self.responses.submit_response(user, survey.id, {"q1": 2})

    def test_us06_response_updates_aggregation(self):
        result = self.auth.register("parent6@example.com")
        user = self.auth.verify_email(result.verification_token)
        survey = self.surveys.create_survey({"questions": [{"type": "scale"}]})
        self.responses.submit_response(user, survey.id, {"q1": 5})
        snapshot = self.aggregations.build_snapshot(survey.id, min_responses=1)
        self.assertEqual(snapshot.metrics["total"], 1)
        statuses = self.responses.list_status(user)
        self.assertEqual(statuses[0]["answered"], True)
        snapshot_default = self.aggregations.build_snapshot_for_survey(survey)
        self.assertEqual(snapshot_default.min_responses, survey.min_responses_default)

    def test_us07_feedback_mode_and_masking(self):
        survey = self.surveys.create_survey({"questions": [{"type": "scale"}]})
        snapshot = self.aggregations.build_snapshot(survey.id, min_responses=2)
        small_n = self.reports.apply_small_n(snapshot)
        self.assertEqual(survey.feedback_mode, "section")
        self.assertEqual(small_n["total"], "X")

    def test_us20_template_validation_and_rendering(self):
        with self.assertRaises(ValidationError):
            self.reports.create_template(None, [])
        survey = self.surveys.create_survey({"questions": [{"type": "scale"}]})
        template = self.reports.create_template(
            survey.id,
            [
                {"type": "text", "content": "Kommun $kommun"},
                {"type": "text", "content": "Visas", "condition": {"min_total": 1}},
            ],
        )
        snapshot = self.aggregations.build_snapshot(survey.id, min_responses=1)
        rendered = self.reports.render(template, snapshot, kommun="Uppsala")
        self.assertIn("Uppsala", rendered["blocks"][0]["content"])
        self.assertEqual(len(rendered["blocks"]), 1)
        rendered_again = self.reports.render(template, snapshot, kommun="Uppsala")
        self.assertEqual(rendered, rendered_again)
        preview = self.reports.preview(template, snapshot, kommun="Uppsala")
        public = self.reports.publish_render(template, snapshot, kommun="Uppsala")
        self.assertEqual(preview, public)

    def test_us21_small_n_banner(self):
        survey = self.surveys.create_survey({"questions": [{"type": "scale"}]})
        template = self.reports.create_template(survey.id, [{"type": "text", "content": "Hej"}])
        snapshot = self.aggregations.build_snapshot(survey.id, min_responses=2)
        payload = self.reports.build_report_payload(template, snapshot, kommun="Test")
        self.assertTrue(payload["small_n_banner"])
        self.assertEqual(payload["metrics"]["total"], "X")
        snapshot_ok = self.aggregations.build_snapshot(survey.id, min_responses=0)
        payload_ok = self.reports.build_report_payload(template, snapshot_ok, kommun="Test")
        self.assertFalse(payload_ok["small_n_banner"])
        self.assertEqual(payload_ok["metrics"]["total"], 0)

    def test_us22_publishing_and_redirect(self):
        publishing = PublishingService(self.stores.responses)
        analyst = self.auth.verify_email(self.auth.register("analyst@example.com").verification_token)
        analyst = self.stores.pii.update_user(analyst.id, role="analyst")
        admin = self.auth.verify_email(self.auth.register("admin2@example.com").verification_token)
        admin = self.stores.pii.update_user(admin.id, role="admin")
        version = publishing.publish(analyst, template_id=1)
        self.assertEqual(version.visibility, "internal")
        version = publishing.set_public_url(analyst, version.id, "rapport-1")
        self.assertEqual(version.canonical_url, "/reports/rapport-1")
        version = publishing.unpublish(admin, version.id)
        self.assertEqual(version.visibility, "internal")
        new_version = publishing.publish(analyst, template_id=1, visibility="public")
        new_version = publishing.set_public_url(analyst, new_version.id, "rapport-2")
        publishing.replace(analyst, version.id, new_version.id)
        replaced = self.stores.responses.get_report_version(version.id)
        self.assertEqual(replaced.replaced_by, new_version.id)
        self.assertTrue(publishing.can_view(None, new_version))
        self.assertFalse(publishing.can_view(None, version))
        self.assertEqual(publishing.resolve_public_url(version.id), "/reports/rapport-2")

    def test_public_site_news_and_library(self):
        item = self.public_site.add_news_item("Nyhet", "Innehåll")
        self.assertEqual(item.title, "Nyhet")
        news = self.public_site.list_news()
        self.assertEqual(len(news), 1)
        survey = self.surveys.create_survey({"questions": [{"type": "scale"}]})
        template = self.reports.create_template(survey.id, [{"type": "text", "content": "Hej"}])
        self.aggregations.build_snapshot(survey.id, min_responses=1)
        analyst = self.auth.verify_email(self.auth.register("lib-analyst@example.com").verification_token)
        analyst = self.stores.pii.update_user(analyst.id, role="analyst")
        publishing = PublishingService(self.stores.responses)
        version = publishing.publish(analyst, template_id=template.id, visibility="public")
        publishing.set_public_url(analyst, version.id, "publik-1")
        library = self.public_site.list_public_reports()
        self.assertEqual(library[0]["canonical_url"], "/reports/publik-1")

    def test_public_site_report_reader_uses_kommun_fallback(self):
        survey = self.surveys.create_survey({"questions": [{"type": "scale"}]})
        template = self.reports.create_template(survey.id, [{"type": "text", "content": "Hej $kommun"}])
        self.aggregations.build_snapshot(survey.id, min_responses=1)
        analyst = self.auth.verify_email(self.auth.register("reader-analyst@example.com").verification_token)
        analyst = self.stores.pii.update_user(analyst.id, role="analyst")
        publishing = PublishingService(self.stores.responses)
        version = publishing.publish(analyst, template_id=template.id, visibility="public")
        publishing.set_public_url(analyst, version.id, "publik-2")
        parent = self.auth.verify_email(self.auth.register("reader-parent@example.com").verification_token)
        BaseProfileService(self.stores.pii).ensure_base_profile(parent, "Kommun X", ["skola"])
        response = self.public_site.read_report("/reports/publik-2", viewer=parent)
        self.assertIn("Kommun X", json.dumps(response["payload"]))
    def test_us08_offer_text_and_matching(self):
        text = self.network.offer_text(3, "kommun A")
        self.assertIn("3", text)
        self.assertIn("kommun A", text)
        user_a = self.auth.verify_email(self.auth.register("match-a@example.com").verification_token)
        user_b = self.auth.verify_email(self.auth.register("match-b@example.com").verification_token)
        user_c = self.auth.verify_email(self.auth.register("match-c@example.com").verification_token)
        base_service = BaseProfileService(self.stores.pii)
        base_service.ensure_base_profile(user_a, "Kommun A", ["sömn"])
        base_service.ensure_base_profile(user_b, "Kommun A", ["sömn"])
        base_service.ensure_base_profile(user_c, "Kommun B", ["skola"])
        summaries = self.network.build_match_summaries()
        summary_contexts = {summary["context"] for summary in summaries}
        self.assertIn("Kommun A (sömn)", summary_contexts)
        for summary in summaries:
            self.assertTrue(all(isinstance(user_id, int) for user_id in summary["user_ids"]))
        self.assertNotIn("match-a@example.com", json.dumps(summaries))

    def test_us09_opt_in_and_outbox(self):
        user_a = self.auth.verify_email(self.auth.register("a@example.com").verification_token)
        user_b = self.auth.verify_email(self.auth.register("b@example.com").verification_token)
        self.network.set_preference(user_a, True)
        self.network.set_preference(user_b, False)
        event = self.network.create_introduction([user_a, user_b], "matchning")
        self.assertEqual(event.recipients, [user_a.id])
        self.assertIsNotNone(event.mail_id)
        outbox = self.stores.pii.list_outbox()
        self.assertEqual(len(outbox), 1)
        self.assertIn("Varför du får detta mail", outbox[0].body)
        self.assertEqual(outbox[0].recipients, event.recipients)

    def test_us09_public_access_blocked(self):
        with self.assertRaises(UnauthorizedError):
            require_role(None, ["parent"])

    def test_us13_ai_prompt_normalized(self):
        request = self.ai.create_request("FREE_PROMPT")
        self.assertEqual(request.prompt, "SUMMARIZE_SURVEY")
        survey = self.surveys.create_survey({"questions": [{"type": "scale"}]})
        snapshot = self.aggregations.build_snapshot(survey.id, min_responses=1)
        self.assertEqual(snapshot.metrics["total"], 0)

    def test_us15_flag_and_redaction(self):
        result = self.auth.register("mod@example.com")
        analyst = self.stores.pii.update_user(result.user.id, verified=True, role="analyst")
        survey = self.surveys.create_survey({"questions": [{"type": "scale"}]})
        response = self.responses.submit_response(analyst, survey.id, {"q": 1}, {"free": "raw"})
        moderation_service = ModerationService(self.stores.responses)
        flag = moderation_service.flag_text(response.id, "pii")
        event = moderation_service.redact_text(flag.id, analyst, "curated")
        curated = moderation_service.add_curated_text(response.id, analyst, "rensad text")
        self.assertEqual(flag.response_id, response.id)
        self.assertEqual(event.flag_id, flag.id)
        self.assertEqual(curated.response_id, response.id)

    def test_us15_public_payload_excludes_raw_text(self):
        survey = self.surveys.create_survey({"questions": [{"type": "scale"}]})
        template = self.reports.create_template(survey.id, [{"type": "text", "content": "Hej"}])
        snapshot = self.aggregations.build_snapshot(survey.id, min_responses=1)
        moderation_service = ModerationService(self.stores.responses)
        result = self.auth.register("curator@example.com")
        curator = self.stores.pii.update_user(result.user.id, verified=True, role="analyst")
        response = self.responses.submit_response(curator, survey.id, {"q": 1}, {"free": "raw"})
        curated = moderation_service.add_curated_text(response_id=response.id, curator=curator, text="kuraterad")
        payload = self.reports.build_report_payload(template, snapshot, kommun="Test", curated_texts=[curated])
        self.assertNotIn("raw_text_fields", json.dumps(payload))
        self.assertIn("kuraterad", json.dumps(payload))

    def test_us19_role_change_audit(self):
        admin = self.auth.verify_email(self.auth.register("admin@example.com").verification_token)
        admin = self.stores.pii.update_user(admin.id, role="admin")
        target = self.auth.verify_email(self.auth.register("user@example.com").verification_token)
        updated = self.admin.change_role(admin, target, "analyst")
        self.assertEqual(updated.role, "analyst")
        self.assertEqual(len(self.stores.pii.list_audit_events()), 1)

    def test_us19_parent_cannot_publish(self):
        publishing = PublishingService(self.stores.responses)
        parent = self.auth.verify_email(self.auth.register("parent-publish@example.com").verification_token)
        with self.assertRaises(UnauthorizedError):
            publishing.publish(parent, template_id=1)

    def test_sec_log_policy_sanitizes_payload(self):
        sanitized = sanitize_log({"payload": "secret", "email": "x", "event": "login"})
        self.assertEqual(sanitized, {"event": "login"})

    def test_sec_rate_limit_login(self):
        self.auth.register("rate@example.com")
        with self.assertRaises(ValidationError):
            self.auth.login("rate@example.com")
        with self.assertRaises(RateLimitError):
            self.auth.login("rate@example.com")

    def test_sec_backup_smoke(self):
        backup_id = self.backup.start_backup()
        self.assertTrue(backup_id.startswith("backup-"))


if __name__ == "__main__":
    unittest.main()
