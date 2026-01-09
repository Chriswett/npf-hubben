import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .domain import UnauthorizedError, ValidationError
from .services import PublicSiteService
from .storage import InMemoryStores


class HealthHandler(BaseHTTPRequestHandler):
    stores: InMemoryStores = InMemoryStores()
    ui_root = Path(__file__).resolve().parent.parent / "frontend"

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
            service = PublicSiteService(self.stores.responses, self.stores.pii)
            items = [{"title": item.title, "body": item.body} for item in service.list_news()]
            self._send_json(200, {"news": items})
            return

        if parsed.path == "/public/reports":
            service = PublicSiteService(self.stores.responses, self.stores.pii)
            self._send_json(200, {"reports": service.list_public_reports()})
            return

        if parsed.path.startswith("/reports/"):
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

    def log_message(self, format, *args):
        return

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Security-Policy", "default-src 'none'")
        self.send_header("X-Frame-Options", "DENY")
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
