from __future__ import annotations

from dataclasses import replace
from typing import Dict, List, Optional

from .domain import (
    AggregationSnapshot,
    AiAnalysisRequest,
    AuditEvent,
    ConsentRecord,
    BaseProfile,
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
    CuratedText,
    User,
)


class PiiStore:
    def __init__(self):
        self._users: Dict[int, User] = {}
        self._sessions: Dict[str, Session] = {}
        self._verification_tokens: Dict[str, int] = {}
        self._base_profiles: Dict[int, BaseProfile] = {}
        self._network_preferences: Dict[int, NetworkPreference] = {}
        self._intro_events: Dict[int, IntroductionEvent] = {}
        self._outbox: Dict[int, MailOutbox] = {}
        self._audit_events: Dict[int, AuditEvent] = {}
        self._consent_records: Dict[int, ConsentRecord] = {}
        self._id_counters: Dict[str, int] = {}

    def next_id(self, name: str) -> int:
        current = self._id_counters.get(name, 0) + 1
        self._id_counters[name] = current
        return current

    # Users / auth (PII)
    def add_user(self, user: User) -> User:
        self._users[user.id] = user
        return user

    def update_user(self, user_id: int, **updates) -> User:
        user = self._users[user_id]
        updated = replace(user, **updates)
        self._users[user_id] = updated
        return updated

    def get_user(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    def add_session(self, session: Session) -> Session:
        self._sessions[session.token] = session
        return session

    def get_session(self, token: str) -> Optional[Session]:
        return self._sessions.get(token)

    def delete_session(self, token: str) -> None:
        self._sessions.pop(token, None)

    def add_verification_token(self, token: str, user_id: int) -> None:
        self._verification_tokens[token] = user_id

    def pop_verification_token(self, token: str) -> Optional[int]:
        return self._verification_tokens.pop(token, None)

    # Base profile (PII)
    def add_base_profile(self, profile: BaseProfile) -> BaseProfile:
        self._base_profiles[profile.user_id] = profile
        return profile

    def get_base_profile(self, user_id: int) -> Optional[BaseProfile]:
        return self._base_profiles.get(user_id)

    def list_base_profiles(self) -> List[BaseProfile]:
        return list(self._base_profiles.values())

    # Network (PII)
    def add_network_preference(self, preference: NetworkPreference) -> NetworkPreference:
        self._network_preferences[preference.user_id] = preference
        return preference

    def get_network_preference(self, user_id: int) -> Optional[NetworkPreference]:
        return self._network_preferences.get(user_id)

    def add_intro_event(self, event: IntroductionEvent) -> IntroductionEvent:
        self._intro_events[event.id] = event
        return event

    def list_intro_events(self) -> List[IntroductionEvent]:
        return list(self._intro_events.values())

    # Outbox (PII)
    def add_outbox_mail(self, mail: MailOutbox) -> MailOutbox:
        self._outbox[mail.id] = mail
        return mail

    def list_outbox(self) -> List[MailOutbox]:
        return list(self._outbox.values())

    # Audit (PII)
    def add_audit_event(self, event: AuditEvent) -> AuditEvent:
        self._audit_events[event.id] = event
        return event

    def list_audit_events(self) -> List[AuditEvent]:
        return list(self._audit_events.values())

    # Consent (PII)
    def add_consent_record(self, record: ConsentRecord) -> ConsentRecord:
        self._consent_records[record.id] = record
        return record

    def list_consent_records(self, user_id: int) -> List[ConsentRecord]:
        return [record for record in self._consent_records.values() if record.user_id == user_id]

    def delete_user_pii(self, user_id: int) -> None:
        self._users.pop(user_id, None)
        self._base_profiles.pop(user_id, None)
        self._network_preferences.pop(user_id, None)
        tokens_to_remove = [token for token, uid in self._verification_tokens.items() if uid == user_id]
        for token in tokens_to_remove:
            self._verification_tokens.pop(token, None)
        sessions_to_remove = [token for token, session in self._sessions.items() if session.user_id == user_id]
        for token in sessions_to_remove:
            self._sessions.pop(token, None)


class ResponseStore:
    def __init__(self):
        self._surveys: Dict[int, Survey] = {}
        self._responses: Dict[int, SurveyResponse] = {}
        self._responses_by_user_survey: Dict[tuple[int, int], int] = {}
        self._aggregations: Dict[int, AggregationSnapshot] = {}
        self._templates: Dict[int, ReportTemplate] = {}
        self._report_versions: Dict[int, ReportVersion] = {}
        self._report_versions_by_url: Dict[str, int] = {}
        self._news: Dict[int, NewsItem] = {}
        self._text_flags: Dict[int, TextFlag] = {}
        self._redaction_events: Dict[int, TextRedactionEvent] = {}
        self._curated_texts: Dict[int, CuratedText] = {}
        self._ai_requests: Dict[int, AiAnalysisRequest] = {}
        self._id_counters: Dict[str, int] = {}

    def next_id(self, name: str) -> int:
        current = self._id_counters.get(name, 0) + 1
        self._id_counters[name] = current
        return current

    # Surveys
    def add_survey(self, survey: Survey) -> Survey:
        self._surveys[survey.id] = survey
        return survey

    def get_survey(self, survey_id: int) -> Optional[Survey]:
        return self._surveys.get(survey_id)

    def list_surveys(self) -> List[Survey]:
        return list(self._surveys.values())

    # Responses
    def add_response(self, response: SurveyResponse) -> SurveyResponse:
        key = (response.user_id, response.survey_id)
        self._responses[response.id] = response
        self._responses_by_user_survey[key] = response.id
        return response

    def get_response_by_user_survey(self, user_id: int, survey_id: int) -> Optional[SurveyResponse]:
        response_id = self._responses_by_user_survey.get((user_id, survey_id))
        if response_id is None:
            return None
        return self._responses.get(response_id)

    def list_responses_for_survey(self, survey_id: int) -> List[SurveyResponse]:
        return [response for response in self._responses.values() if response.survey_id == survey_id]

    # Aggregations
    def upsert_aggregation(self, snapshot: AggregationSnapshot) -> AggregationSnapshot:
        self._aggregations[snapshot.survey_id] = snapshot
        return snapshot

    def get_aggregation(self, survey_id: int) -> Optional[AggregationSnapshot]:
        return self._aggregations.get(survey_id)

    # Reports
    def add_report_template(self, template: ReportTemplate) -> ReportTemplate:
        self._templates[template.id] = template
        return template

    def get_report_template(self, template_id: int) -> Optional[ReportTemplate]:
        return self._templates.get(template_id)

    def add_report_version(self, version: ReportVersion) -> ReportVersion:
        self._report_versions[version.id] = version
        if version.canonical_url:
            self._report_versions_by_url[version.canonical_url] = version.id
        return version

    def update_report_version(self, version_id: int, **updates) -> ReportVersion:
        version = self._report_versions[version_id]
        updated = replace(version, **updates)
        self._report_versions[version_id] = updated
        if updated.canonical_url:
            self._report_versions_by_url[updated.canonical_url] = updated.id
        return updated

    def get_report_version(self, version_id: int) -> Optional[ReportVersion]:
        return self._report_versions.get(version_id)

    def get_report_version_by_url(self, url: str) -> Optional[ReportVersion]:
        version_id = self._report_versions_by_url.get(url)
        if version_id is None:
            return None
        return self._report_versions.get(version_id)

    def list_report_versions(self) -> List[ReportVersion]:
        return list(self._report_versions.values())

    # News
    def add_news_item(self, item: NewsItem) -> NewsItem:
        self._news[item.id] = item
        return item

    def list_news(self) -> List[NewsItem]:
        return list(self._news.values())

    # Moderation
    def add_text_flag(self, flag: TextFlag) -> TextFlag:
        self._text_flags[flag.id] = flag
        return flag

    def add_redaction_event(self, event: TextRedactionEvent) -> TextRedactionEvent:
        self._redaction_events[event.id] = event
        return event

    def list_text_flags(self) -> List[TextFlag]:
        return list(self._text_flags.values())

    def list_redaction_events(self) -> List[TextRedactionEvent]:
        return list(self._redaction_events.values())

    def add_curated_text(self, curated_text: CuratedText) -> CuratedText:
        self._curated_texts[curated_text.id] = curated_text
        return curated_text

    def list_curated_texts(self) -> List[CuratedText]:
        return list(self._curated_texts.values())

    # AI requests
    def add_ai_request(self, request: AiAnalysisRequest) -> AiAnalysisRequest:
        self._ai_requests[request.id] = request
        return request

    def list_ai_requests(self) -> List[AiAnalysisRequest]:
        return list(self._ai_requests.values())

    def delete_user_responses(self, user_id: int) -> None:
        response_ids = [rid for rid, response in self._responses.items() if response.user_id == user_id]
        for response_id in response_ids:
            response = self._responses.pop(response_id, None)
            if response:
                self._responses_by_user_survey.pop((response.user_id, response.survey_id), None)
            curated_ids = [cid for cid, curated in self._curated_texts.items() if curated.response_id == response_id]
            for curated_id in curated_ids:
                self._curated_texts.pop(curated_id, None)
            flag_ids = [fid for fid, flag in self._text_flags.items() if flag.response_id == response_id]
            for flag_id in flag_ids:
                self._text_flags.pop(flag_id, None)


class InMemoryStores:
    def __init__(self):
        self.pii = PiiStore()
        self.responses = ResponseStore()
