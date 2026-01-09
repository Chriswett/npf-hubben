import json
import socket
import threading

import pytest

pytest.importorskip("playwright.sync_api")

from playwright.sync_api import sync_playwright

from backend.security import RateLimiter
from backend.server import create_server
from backend.services import (
    AggregationService,
    AuthService,
    PublishingService,
    ReportService,
    SurveyService,
)
from backend.storage import InMemoryStores


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("", 0))
        return sock.getsockname()[1]


def _seed_public_report(stores: InMemoryStores) -> None:
    surveys = SurveyService(stores.responses)
    reports = ReportService(stores.responses)
    aggregations = AggregationService(stores.responses)
    auth = AuthService(stores.pii, RateLimiter())
    analyst = auth.verify_email(auth.register("e2e-analyst@example.com").verification_token)
    analyst = stores.pii.update_user(analyst.id, role="analyst")
    publishing = PublishingService(stores.responses)

    survey = surveys.create_survey({"questions": [{"type": "scale"}]})
    template = reports.create_template(survey.id, [{"type": "text", "content": "Hej $kommun"}])
    aggregations.build_snapshot(survey.id, min_responses=2)

    version = publishing.publish(analyst, template_id=template.id, visibility="public")
    publishing.set_public_url(analyst, version.id, "rapport-e2e")

    old_version = publishing.publish(analyst, template_id=template.id, visibility="public")
    publishing.set_public_url(analyst, old_version.id, "rapport-old")
    new_version = publishing.publish(analyst, template_id=template.id, visibility="public")
    publishing.set_public_url(analyst, new_version.id, "rapport-new")
    publishing.replace(analyst, old_version.id, new_version.id)


def _run_server(server) -> None:
    server.serve_forever()


@pytest.fixture(scope="module")
def server_url() -> str:
    stores = InMemoryStores()
    _seed_public_report(stores)
    port = _free_port()
    server = create_server("127.0.0.1", port, stores=stores)
    thread = threading.Thread(target=_run_server, args=(server,), daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=1)


def test_public_report_small_n_banner(server_url: str) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(f"{server_url}/reports/rapport-e2e?kommun=Test")
        body_text = page.evaluate("document.body.textContent")
        data = json.loads(body_text)
        payload = data["payload"]
        assert payload["metrics"]["total"] == "X"
        assert payload["small_n_banner"] is True
        browser.close()


def test_public_report_redirect(server_url: str) -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.goto(f"{server_url}/reports/rapport-old?kommun=Test")
        assert page.url.endswith("/reports/rapport-new?kommun=Test")
        browser.close()
