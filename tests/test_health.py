import json
import threading
import unittest
from http.client import HTTPConnection

from backend.server import create_server


class HealthEndpointTests(unittest.TestCase):
    def setUp(self):
        self.server = create_server(host="127.0.0.1", port=0)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        self.host, self.port = self.server.server_address

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1)

    def test_health_endpoint_returns_ok(self):
        connection = HTTPConnection(self.host, self.port)
        connection.request("GET", "/health")
        response = connection.getresponse()
        body = response.read().decode("utf-8")

        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(body), {"status": "ok"})
        self.assertEqual(response.getheader("Content-Security-Policy"), "default-src 'none'")
        self.assertEqual(response.getheader("X-Frame-Options"), "DENY")

    def test_version_endpoint_returns_version(self):
        connection = HTTPConnection(self.host, self.port)
        connection.request("GET", "/version")
        response = connection.getresponse()
        body = response.read().decode("utf-8")

        self.assertEqual(response.status, 200)
        self.assertEqual(json.loads(body), {"version": "0.1.0"})

    def test_unknown_path_returns_404(self):
        connection = HTTPConnection(self.host, self.port)
        connection.request("GET", "/missing")
        response = connection.getresponse()
        body = response.read().decode("utf-8")

        self.assertEqual(response.status, 404)
        self.assertEqual(json.loads(body), {"error": "not_found"})


if __name__ == "__main__":
    unittest.main()
