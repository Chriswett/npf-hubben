import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return

        if self.path == "/version":
            self._send_json(200, {"version": "0.1.0"})
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


def create_server(host="0.0.0.0", port=8000):
    return ThreadingHTTPServer((host, port), HealthHandler)


def run(host="0.0.0.0", port=8000):
    server = create_server(host, port)
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
