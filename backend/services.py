from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .domain import (
    AggregationSnapshot,
    BaseProfile,
    ConflictError,
    IntroductionEvent,
    MailOutbox,
    NetworkPreference,
    ReportTemplate,
    ReportVersion,
    Session,
    Survey,
    SurveyResponse,
    TextFlag,
    TextRedactionEvent,
    CuratedText,
    AiAnalysisRequest,
    AuditEvent,
    User,
    ValidationError,
)
from .security import RateLimiter, require_role
from .storage import PiiStore, ResponseStore


ALLOWED_QUESTION_TYPES = {"scale", "multichoice", "singlechoice", "short_text", "long_text"}


@dataclass
class RegisterResult:
    user: User
    verification_token: str


class AuthService:
    def __init__(self, store: PiiStore, rate_limiter: RateLimiter):
        self.store = store
        self.rate_limiter = rate_limiter
        self._verification_tokens: Dict[str, int] = {}

    def register(self, email: str) -> RegisterResult:
        if not email or "@" not in email:
            raise ValidationError("invalid_email")
        if self.store.get_user_by_email(email):
            raise ConflictError("email_exists")
        user = User(id=self.store.next_id("user"), email=email, role="parent", verified=False)
        self.store.add_user(user)
        token = secrets.token_hex(8)
        self._verification_tokens[token] = user.id
        return RegisterResult(user=user, verification_token=token)

    def verify_email(self, token: str) -> User:
        if token not in self._verification_tokens:
            raise ValidationError("invalid_token")
        user_id = self._verification_tokens.pop(token)
        return self.store.update_user(user_id, verified=True)

    def login(self, email: str) -> Session:
        self.rate_limiter.register_attempt(email)
        user = self.store.get_user_by_email(email)
        if user is None or not user.verified:
            raise ValidationError("invalid_credentials")
        token = secrets.token_hex(16)
        session = Session(token=token, user_id=user.id)
        self.store.add_session(session)
        return session


class SurveyService:
    def __init__(self, store: ResponseStore):
        self.store = store

    def validate_schema(self, schema: Dict[str, Any]) -> None:
        questions = schema.get("questions", [])
        if not questions:
            raise ValidationError("empty_schema")
        for question in questions:
            q_type = question.get("type")
            if q_type not in ALLOWED_QUESTION_TYPES:
                raise ValidationError("unsupported_question_type")

    def create_survey(self, schema: Dict[str, Any], base_block_policy: str = "enabled") -> Survey:
        self.validate_schema(schema)
        survey = Survey(id=self.store.next_id("survey"), schema=schema, base_block_policy=base_block_policy)
        self.store.add_survey(survey)
        return survey

    def list_open_surveys(self) -> List[Survey]:
        return self.store.list_surveys()


class BaseProfileService:
    def __init__(self, store: PiiStore):
        self.store = store

    def ensure_base_profile(self, user: User, kommun: str, categories: Optional[List[str]] = None) -> BaseProfile:
        profile = self.store.get_base_profile(user.id)
        if profile:
            return profile
        profile = BaseProfile(
            id=self.store.next_id("base_profile"),
            user_id=user.id,
            kommun=kommun,
            categories=categories or [],
        )
        self.store.add_base_profile(profile)
        return profile


class ResponseService:
    def __init__(self, store: ResponseStore):
        self.store = store

    def submit_response(
        self,
        user: User,
        survey_id: int,
        answers: Dict[str, Any],
        raw_text_fields: Optional[Dict[str, str]] = None,
    ) -> SurveyResponse:
        if not user.verified:
            raise ValidationError("unverified_user")
        if self.store.get_response_by_user_survey(user.id, survey_id):
            raise ConflictError("duplicate_response")
        response = SurveyResponse(
            id=self.store.next_id("response"),
            survey_id=survey_id,
            user_id=user.id,
            answers=answers,
            raw_text_fields=raw_text_fields or {},
        )
        self.store.add_response(response)
        return response

    def has_answered(self, user: User, survey_id: int) -> bool:
        return self.store.get_response_by_user_survey(user.id, survey_id) is not None

    def list_status(self, user: User) -> List[Dict[str, Any]]:
        statuses = []
        for survey in self.store.list_surveys():
            statuses.append({"survey_id": survey.id, "answered": self.has_answered(user, survey.id)})
        return statuses


class AggregationService:
    def __init__(self, store: ResponseStore):
        self.store = store

    def build_snapshot_for_survey(self, survey: Survey) -> AggregationSnapshot:
        return self.build_snapshot(survey.id, min_responses=survey.min_responses_default)

    def build_snapshot(self, survey_id: int, min_responses: int) -> AggregationSnapshot:
        responses = self.store.list_responses_for_survey(survey_id)
        total = len(responses)
        data_version_hash = hashlib.sha256(json.dumps([r.id for r in responses]).encode("utf-8")).hexdigest()
        metrics = {"total": total}
        snapshot = AggregationSnapshot(
            survey_id=survey_id,
            data_version_hash=data_version_hash,
            metrics=metrics,
            min_responses=min_responses,
        )
        self.store.upsert_aggregation(snapshot)
        return snapshot


class ReportService:
    def __init__(self, store: ResponseStore):
        self.store = store

    def create_template(self, survey_id: int, blocks: List[Dict[str, Any]]) -> ReportTemplate:
        if survey_id is None:
            raise ValidationError("survey_id_required")
        template = ReportTemplate(id=self.store.next_id("template"), survey_id=survey_id, blocks=blocks)
        self.store.add_report_template(template)
        return template

    def render(self, template: ReportTemplate, snapshot: AggregationSnapshot, kommun: str) -> Dict[str, Any]:
        placeholders = {
            "$kommun": kommun,
            "$antal_respondenter": str(snapshot.metrics.get("total", 0)),
        }
        rendered_blocks = []
        for block in template.blocks:
            if not self._condition_allowed(block, snapshot):
                continue
            content = block.get("content", "")
            for key, value in placeholders.items():
                content = content.replace(key, value)
            rendered_blocks.append({"type": block.get("type", "text"), "content": content})
        return {"blocks": rendered_blocks, "data_version_hash": snapshot.data_version_hash}

    def preview(self, template: ReportTemplate, snapshot: AggregationSnapshot, kommun: str) -> Dict[str, Any]:
        return self.render(template, snapshot, kommun)

    def publish_render(self, template: ReportTemplate, snapshot: AggregationSnapshot, kommun: str) -> Dict[str, Any]:
        return self.render(template, snapshot, kommun)

    def _condition_allowed(self, block: Dict[str, Any], snapshot: AggregationSnapshot) -> bool:
        condition = block.get("condition")
        if not condition:
            return True
        min_total = condition.get("min_total")
        if min_total is None:
            return True
        return snapshot.metrics.get("total", 0) >= min_total

    def apply_small_n(self, snapshot: AggregationSnapshot) -> Dict[str, Any]:
        total = snapshot.metrics.get("total", 0)
        masked = total < snapshot.min_responses
        return {"total": "X" if masked else total, "masked": masked}

    def build_report_payload(
        self,
        template: ReportTemplate,
        snapshot: AggregationSnapshot,
        kommun: str,
        curated_texts: Optional[List[CuratedText]] = None,
    ) -> Dict[str, Any]:
        rendered = self.render(template, snapshot, kommun)
        small_n = self.apply_small_n(snapshot)
        curated_payload = [entry.text for entry in (curated_texts or [])]
        return {
            "kommun": kommun,
            "blocks": rendered["blocks"],
            "data_version_hash": rendered["data_version_hash"],
            "metrics": {"total": small_n["total"]},
            "small_n_banner": small_n["masked"],
            "curated_texts": curated_payload,
        }


class PublishingService:
    def __init__(self, store: ResponseStore):
        self.store = store

    def publish(self, actor: User, template_id: int, visibility: str = "internal") -> ReportVersion:
        require_role(actor, ["analyst", "admin"])
        version = ReportVersion(id=self.store.next_id("report_version"), template_id=template_id, visibility=visibility)
        return self.store.add_report_version(version)

    def set_public_url(self, actor: User, version_id: int, slug: str) -> ReportVersion:
        require_role(actor, ["analyst", "admin"])
        url = f"/reports/{slug}"
        return self.store.update_report_version(version_id, canonical_url=url)

    def replace(self, actor: User, old_version_id: int, new_version_id: int) -> None:
        require_role(actor, ["analyst", "admin"])
        self.store.update_report_version(old_version_id, replaced_by=new_version_id)

    def unpublish(self, actor: User, version_id: int) -> ReportVersion:
        require_role(actor, ["admin"])
        return self.store.update_report_version(version_id, visibility="internal")

    def can_view(self, actor: Optional[User], version: ReportVersion) -> bool:
        if version.visibility == "public":
            return True
        return actor is not None

    def resolve_public_url(self, version_id: int) -> str:
        version = self.store.get_report_version(version_id)
        if version is None:
            raise ValidationError("report_version_not_found")
        if version.replaced_by:
            replacement = self.store.get_report_version(version.replaced_by)
            if replacement and replacement.canonical_url:
                return replacement.canonical_url
        if not version.canonical_url:
            raise ValidationError("canonical_url_missing")
        return version.canonical_url


class ModerationService:
    def __init__(self, store: ResponseStore):
        self.store = store

    def flag_text(self, response_id: int, reason: str) -> TextFlag:
        flag = TextFlag(id=self.store.next_id("text_flag"), response_id=response_id, reason=reason)
        self.store.add_text_flag(flag)
        return flag

    def redact_text(self, flag_id: int, curator: User, note: str) -> TextRedactionEvent:
        require_role(curator, ["analyst", "admin"])
        event = TextRedactionEvent(
            id=self.store.next_id("redaction_event"), flag_id=flag_id, curator_id=curator.id, note=note
        )
        self.store.add_redaction_event(event)
        return event

    def add_curated_text(self, response_id: int, curator: User, text: str) -> CuratedText:
        require_role(curator, ["analyst", "admin"])
        curated = CuratedText(id=self.store.next_id("curated_text"), response_id=response_id, text=text)
        self.store.add_curated_text(curated)
        return curated

    def list_curated_texts(self) -> List[CuratedText]:
        return self.store.list_curated_texts()


class NetworkService:
    def __init__(self, store: PiiStore):
        self.store = store

    def set_preference(self, user: User, opt_in: bool) -> NetworkPreference:
        preference = NetworkPreference(id=self.store.next_id("network_pref"), user_id=user.id, opt_in=opt_in)
        self.store.add_network_preference(preference)
        return preference

    def create_introduction(self, recipients: List[User], reason: str) -> IntroductionEvent:
        eligible = []
        for user in recipients:
            preference = self.store.get_network_preference(user.id)
            if preference and preference.opt_in:
                eligible.append(user.id)
        event = IntroductionEvent(id=self.store.next_id("intro_event"), recipients=eligible, reason=reason)
        self.store.add_intro_event(event)
        mail = MailOutbox(
            id=self.store.next_id("mail"),
            recipients=eligible,
            subject="Introduktion till andra föräldrar",
            body=f"Varför du får detta mail: {reason}",
        )
        self.store.add_outbox_mail(mail)
        return event

    def offer_text(self, count: int, context: str) -> str:
        return f"Vi har hittat {count} andra i {context}."


class AiService:
    def __init__(self, store: ResponseStore):
        self.store = store

    def create_request(self, prompt: str) -> AiAnalysisRequest:
        allowed_prompt = "SUMMARIZE_SURVEY"
        if prompt != allowed_prompt:
            prompt = allowed_prompt
        request = AiAnalysisRequest(id=self.store.next_id("ai_request"), prompt=prompt)
        self.store.add_ai_request(request)
        return request


class BackupService:
    def __init__(self, store: ResponseStore):
        self.store = store

    def start_backup(self) -> str:
        return f"backup-{self.store.next_id('backup')}"


class AdminService:
    def __init__(self, store: PiiStore):
        self.store = store

    def change_role(self, actor: User, target_user: User, new_role: str) -> User:
        require_role(actor, ["admin"])
        updated = self.store.update_user(target_user.id, role=new_role)
        event = AuditEvent(
            id=self.store.next_id("audit"),
            actor_id=actor.id,
            target_user_id=target_user.id,
            action=f"role_change:{new_role}",
        )
        self.store.add_audit_event(event)
        return updated


class SurveyFlowService:
    def __init__(self, pii_store: PiiStore, response_store: ResponseStore):
        self.pii_store = pii_store
        self.response_store = response_store

    def needs_base_block(self, user: User) -> bool:
        return self.pii_store.get_base_profile(user.id) is None

    def start_survey(self, user: User, survey_id: int) -> Dict[str, Any]:
        survey = self.response_store.get_survey(survey_id)
        if not survey:
            raise ValidationError("survey_not_found")
        return {
            "survey_id": survey.id,
            "needs_base_block": survey.base_block_policy == "enabled" and self.needs_base_block(user),
        }
