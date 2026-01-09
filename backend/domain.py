from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class DomainError(Exception):
    pass


class ValidationError(DomainError):
    pass


class UnauthorizedError(DomainError):
    pass


class ConflictError(DomainError):
    pass


class RateLimitError(DomainError):
    pass


@dataclass(frozen=True)
class User:
    id: int
    email: str
    role: str = "parent"
    verified: bool = False


@dataclass(frozen=True)
class Session:
    token: str
    user_id: int
    csrf_token: str


@dataclass(frozen=True)
class Survey:
    id: int
    schema: Dict[str, Any]
    base_block_policy: str = "enabled"
    feedback_mode: str = "section"
    min_responses_default: int = 5


@dataclass(frozen=True)
class BaseProfile:
    id: int
    user_id: int
    kommun: str
    categories: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class SurveyResponse:
    id: int
    survey_id: int
    user_id: int
    answers: Dict[str, Any]
    raw_text_fields: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AggregationSnapshot:
    survey_id: int
    data_version_hash: str
    metrics: Dict[str, Any]
    min_responses: int


@dataclass(frozen=True)
class ReportTemplate:
    id: int
    survey_id: int
    blocks: List[Dict[str, Any]]


@dataclass(frozen=True)
class ReportVersion:
    id: int
    template_id: int
    visibility: str = "internal"
    canonical_url: Optional[str] = None
    replaced_by: Optional[int] = None


@dataclass(frozen=True)
class NewsItem:
    id: int
    title: str
    body: str


@dataclass(frozen=True)
class NetworkPreference:
    id: int
    user_id: int
    opt_in: bool


@dataclass(frozen=True)
class IntroductionEvent:
    id: int
    recipients: List[int]
    reason: str
    mail_id: Optional[int] = None


@dataclass(frozen=True)
class TextFlag:
    id: int
    response_id: int
    reason: str


@dataclass(frozen=True)
class TextRedactionEvent:
    id: int
    flag_id: int
    curator_id: int
    note: str


@dataclass(frozen=True)
class CuratedText:
    id: int
    response_id: int
    text: str


@dataclass(frozen=True)
class MailOutbox:
    id: int
    recipients: List[int]
    subject: str
    body: str


@dataclass(frozen=True)
class AiAnalysisRequest:
    id: int
    prompt: str


@dataclass(frozen=True)
class AuditEvent:
    id: int
    actor_id: int
    target_user_id: int
    action: str


@dataclass(frozen=True)
class ConsentRecord:
    id: int
    user_id: int
    consent_type: str
    version: str
    status: str
    timestamp: str
