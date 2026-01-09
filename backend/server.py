import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .domain import RateLimitError, UnauthorizedError, ValidationError
from .security import RateLimiter, require_role
from .services import (
    AuthService,
    BaseProfileService,
    ConsentService,
    PublishingService,
    PublicSiteService,
    ReportService,
    ResponseService,
    SurveyService,
    AccountService,
)
from .storage import InMemoryStores


class HealthHandler(BaseHTTPRequestHandler):
    stores: InMemoryStores = InMemoryStores()
    ui_root = Path(__file__).resolve().parent.parent / "frontend"
    public_rate_limiter = RateLimiter(max_attempts=200)
    auth_rate_limiter = RateLimiter(max_attempts=5)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path in {"/ui", "/ui/"}:
            self._send_file(self.ui_root / "index.html")
            return

        if parsed.path.startswith("/ui/"):
            relative = parsed.path[len("/ui/") :]
            target = (self.ui_root / relative).resolve()
            if self.ui_root not in target.parents and target != self.ui_root:
                self._send_json(404, {"error": "not_found"})
                return
            if not target.is_file():
                self._send_json(404, {"error": "not_found"})
                return
            self._send_file(target)
            return

        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return

        if self.path == "/version":
            self._send_json(200, {"version": "0.1.0"})
            return

        if parsed.path == "/public/news":
            if not self._allow_public_request("news"):
                return
            service = PublicSiteService(self.stores.responses, self.stores.pii)
            items = [{"title": item.title, "body": item.body} for item in service.list_news()]
            self._send_json(200, {"news": items})
            return

        if parsed.path == "/public/reports":
            if not self._allow_public_request("reports"):
                return
            service = PublicSiteService(self.stores.responses, self.stores.pii)
            self._send_json(200, {"reports": service.list_public_reports()})
            return

        if parsed.path.startswith("/reports/"):
            if not self._allow_public_request("report_read"):
                return
            slug = parsed.path.split("/reports/", 1)[1]
            service = PublicSiteService(self.stores.responses, self.stores.pii)
            kommun = parse_qs(parsed.query).get("kommun", [None])[0]
            try:
                result = service.read_report(f"/reports/{slug}", kommun=kommun)
            except ValidationError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            except UnauthorizedError:
                self._send_json(403, {"error": "forbidden"})
                return
            if "redirect" in result:
                self.send_response(302)
                self.send_header("Location", result["redirect"])
                self.send_header("Content-Security-Policy", "default-src 'none'")
                self.send_header("X-Frame-Options", "DENY")
                self.end_headers()
                return
            self._send_json(200, result)
            return

        self._send_json(404, {"error": "not_found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/register":
            payload = self._read_json()
            if payload is None:
                return
            auth = AuthService(self.stores.pii, self.auth_rate_limiter)
            try:
                result = auth.register(payload.get("email", ""))
            except ValidationError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            self._send_json(200, {"user_id": result.user.id, "verification_token": result.verification_token})
            return

        if parsed.path == "/api/verify":
            payload = self._read_json()
            if payload is None:
                return
            auth = AuthService(self.stores.pii, self.auth_rate_limiter)
            try:
                user = auth.verify_email(payload.get("token", ""))
            except ValidationError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            self._send_json(200, {"user_id": user.id, "verified": user.verified})
            return

        if parsed.path == "/api/login":
            payload = self._read_json()
            if payload is None:
                return
            auth = AuthService(self.stores.pii, self.auth_rate_limiter)
            try:
                session = auth.login(payload.get("email", ""))
            except (ValidationError, RateLimitError) as exc:
                status = 429 if isinstance(exc, RateLimitError) else 400
                self._send_json(status, {"error": str(exc)})
                return
            cookies = self._session_cookie_headers(session.token, session.csrf_token)
            self._send_json(200, {"session": "ok"}, cookies=cookies)
            return

        if parsed.path == "/api/logout":
            session = self._get_session()
            if session:
                self.stores.pii.delete_session(session.token)
            cookies = self._clear_session_cookie_headers()
            self._send_json(200, {"logout": "ok"}, cookies=cookies)
            return

        if parsed.path == "/api/base-profile":
            user = self._require_user()
            if user is None:
                return
            if not self._require_csrf():
                return
            payload = self._read_json()
            if payload is None:
                return
            base_profiles = BaseProfileService(self.stores.pii)
            profile = base_profiles.ensure_base_profile(
                user, payload.get("kommun", ""), payload.get("categories", []) or []
            )
            self._send_json(200, {"base_profile_id": profile.id, "kommun": profile.kommun})
            return

        if parsed.path == "/api/consents":
            user = self._require_user()
            if user is None:
                return
            if not self._require_csrf():
                return
            payload = self._read_json()
            if payload is None:
                return
            consent_type = payload.get("consent_type", "")
            version = payload.get("version", "")
            status = payload.get("status", "granted")
            consents = ConsentService(self.stores.pii)
            record = consents.record_consent(user, consent_type, version, status=status)
            self._send_json(200, {"consent_id": record.id, "status": record.status})
            return

        if parsed.path == "/api/consents/revoke":
            user = self._require_user()
            if user is None:
                return
            if not self._require_csrf():
                return
            payload = self._read_json()
            if payload is None:
                return
            consent_type = payload.get("consent_type", "")
            version = payload.get("version", "")
            consents = ConsentService(self.stores.pii)
            record = consents.revoke_consent(user, consent_type, version)
            self._send_json(200, {"consent_id": record.id, "status": record.status})
            return

        if parsed.path == "/api/account/delete":
            user = self._require_user()
            if user is None:
                return
            if not self._require_csrf():
                return
            account = AccountService(self.stores.pii, self.stores.responses)
            try:
                account.delete_account(user, user.id)
            except UnauthorizedError:
                self._send_json(403, {"error": "forbidden"})
                return
            self._send_json(200, {"deleted": "ok"})
            return

        if parsed.path == "/api/surveys":
            user = self._require_user()
            if user is None:
                return
            if not self._require_csrf():
                return
            payload = self._read_json()
            if payload is None:
                return
            surveys = SurveyService(self.stores.responses)
            try:
                require_role(user, ["analyst", "admin"])
                survey = surveys.create_survey(payload.get("schema", {}), payload.get("base_block_policy", "enabled"))
            except UnauthorizedError:
                self._send_json(403, {"error": "forbidden"})
                return
            except ValidationError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            self._send_json(200, {"survey_id": survey.id})
            return

        if parsed.path.startswith("/api/surveys/") and parsed.path.endswith("/responses"):
            user = self._require_user()
            if user is None:
                return
            if not self._require_csrf():
                return
            payload = self._read_json()
            if payload is None:
                return
            survey_id = self._parse_int_path(parsed.path, prefix="/api/surveys/", suffix="/responses")
            if survey_id is None:
                self._send_json(400, {"error": "invalid_survey"})
                return
            responses = ResponseService(self.stores.responses)
            try:
                response = responses.submit_response(
                    user,
                    survey_id,
                    payload.get("answers", {}),
                    payload.get("raw_text_fields", {}),
                )
            except (ValidationError, UnauthorizedError) as exc:
                self._send_json(400, {"error": str(exc)})
                return
            self._send_json(200, {"response_id": response.id})
            return

        if parsed.path == "/api/reports/templates":
            user = self._require_user()
            if user is None:
                return
            if not self._require_csrf():
                return
            payload = self._read_json()
            if payload is None:
                return
            reports = ReportService(self.stores.responses)
            try:
                require_role(user, ["analyst", "admin"])
                template = reports.create_template(payload.get("survey_id"), payload.get("blocks", []))
            except UnauthorizedError:
                self._send_json(403, {"error": "forbidden"})
                return
            except ValidationError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            self._send_json(200, {"template_id": template.id})
            return

        if parsed.path == "/api/reports/publish":
            user = self._require_user()
            if user is None:
                return
            if not self._require_csrf():
                return
            payload = self._read_json()
            if payload is None:
                return
            publishing = PublishingService(self.stores.responses)
            try:
                version = publishing.publish(
                    user,
                    template_id=payload.get("template_id"),
                    visibility=payload.get("visibility", "internal"),
                )
            except UnauthorizedError:
                self._send_json(403, {"error": "forbidden"})
                return
            except ValidationError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            self._send_json(200, {"version_id": version.id})
            return

        if parsed.path.startswith("/api/reports/") and parsed.path.endswith("/url"):
            user = self._require_user()
            if user is None:
                return
            if not self._require_csrf():
                return
            payload = self._read_json()
            if payload is None:
                return
            version_id = self._parse_int_path(parsed.path, prefix="/api/reports/", suffix="/url")
            if version_id is None:
                self._send_json(400, {"error": "invalid_report_version"})
                return
            publishing = PublishingService(self.stores.responses)
            try:
                version = publishing.set_public_url(user, version_id, payload.get("slug", ""))
            except UnauthorizedError:
                self._send_json(403, {"error": "forbidden"})
                return
            except ValidationError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            self._send_json(200, {"canonical_url": version.canonical_url})
            return

        if parsed.path.startswith("/api/reports/") and parsed.path.endswith("/replace"):
            user = self._require_user()
            if user is None:
                return
            if not self._require_csrf():
                return
            payload = self._read_json()
            if payload is None:
                return
            version_id = self._parse_int_path(parsed.path, prefix="/api/reports/", suffix="/replace")
            if version_id is None:
                self._send_json(400, {"error": "invalid_report_version"})
                return
            publishing = PublishingService(self.stores.responses)
            try:
                publishing.replace(user, version_id, payload.get("new_version_id"))
            except UnauthorizedError:
                self._send_json(403, {"error": "forbidden"})
                return
            except ValidationError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            self._send_json(200, {"replaced": "ok"})
            return

        if parsed.path.startswith("/api/reports/") and parsed.path.endswith("/unpublish"):
            user = self._require_user()
            if user is None:
                return
            if not self._require_csrf():
                return
            version_id = self._parse_int_path(parsed.path, prefix="/api/reports/", suffix="/unpublish")
            if version_id is None:
                self._send_json(400, {"error": "invalid_report_version"})
                return
            publishing = PublishingService(self.stores.responses)
            try:
                version = publishing.unpublish(user, version_id)
            except UnauthorizedError:
                self._send_json(403, {"error": "forbidden"})
                return
            except ValidationError as exc:
                self._send_json(400, {"error": str(exc)})
                return
            self._send_json(200, {"visibility": version.visibility})
            return

        self._send_json(404, {"error": "not_found"})

    def log_message(self, format, *args):
        return

    def _send_json(self, status, payload, cookies=None):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Security-Policy", "default-src 'none'")
        self.send_header("X-Frame-Options", "DENY")
        if cookies:
            for cookie in cookies:
                self.send_header("Set-Cookie", cookie)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        content = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:",
        )
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            self._send_json(400, {"error": "empty_body"})
            return None
        body = self.rfile.read(length)
        try:
            return json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid_json"})
            return None

    def _parse_cookies(self) -> SimpleCookie:
        cookie_header = self.headers.get("Cookie", "")
        cookies = SimpleCookie()
        cookies.load(cookie_header)
        return cookies

    def _get_session(self):
        cookies = self._parse_cookies()
        if "session" not in cookies:
            return None
        token = cookies["session"].value
        return self.stores.pii.get_session(token)

    def _require_user(self):
        session = self._get_session()
        if session is None:
            self._send_json(401, {"error": "unauthorized"})
            return None
        user = self.stores.pii.get_user(session.user_id)
        if user is None:
            self._send_json(401, {"error": "unauthorized"})
            return None
        return user

    def _require_csrf(self) -> bool:
        session = self._get_session()
        if session is None:
            self._send_json(401, {"error": "unauthorized"})
            return False
        csrf_header = self.headers.get("X-CSRF-Token")
        if not csrf_header or csrf_header != session.csrf_token:
            self._send_json(403, {"error": "csrf_required"})
            return False
        return True

    def _session_cookie_headers(self, token: str, csrf_token: str) -> list[str]:
        return [
            f"session={token}; Path=/; HttpOnly; SameSite=Strict; Secure",
            f"csrf_token={csrf_token}; Path=/; SameSite=Strict; Secure",
        ]

    def _clear_session_cookie_headers(self) -> list[str]:
        return [
            "session=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict; Secure",
            "csrf_token=; Path=/; Max-Age=0; SameSite=Strict; Secure",
        ]

    def _parse_int_path(self, path: str, prefix: str, suffix: str) -> int | None:
        if not path.startswith(prefix) or not path.endswith(suffix):
            return None
        segment = path[len(prefix) : -len(suffix)]
        if not segment.isdigit():
            return None
        return int(segment)

    def _allow_public_request(self, key: str) -> bool:
        client = self.client_address[0] if self.client_address else "unknown"
        try:
            self.public_rate_limiter.register_attempt(f"{client}:{key}")
        except RateLimitError:
            self._send_json(429, {"error": "rate_limit_exceeded"})
            return False
        return True


def create_server(host="0.0.0.0", port=8000, stores: InMemoryStores | None = None):
    handler = HealthHandler
    if stores is not None:
        handler = type("AppHandler", (HealthHandler,), {"stores": stores})
    return ThreadingHTTPServer((host, port), handler)


def run(host="0.0.0.0", port=8000, stores: InMemoryStores | None = None):
    server = create_server(host, port, stores=stores)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def parse_args():
    parser = argparse.ArgumentParser(description="NPF Hubben backend server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(host=args.host, port=args.port)
