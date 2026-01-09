import json
import threading
import unittest
from http.client import HTTPConnection

from backend.server import create_server
from backend.storage import InMemoryStores


class ApiEndpointTests(unittest.TestCase):
    def setUp(self):
        self.stores = InMemoryStores()
        self.server = create_server(host="127.0.0.1", port=0, stores=self.stores)
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        self.host, self.port = self.server.server_address

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1)

    def _request(self, method, path, body=None, headers=None):
        connection = HTTPConnection(self.host, self.port)
        payload = json.dumps(body).encode("utf-8") if body is not None else None
        request_headers = {"Content-Type": "application/json"}
        if headers:
            request_headers.update(headers)
        connection.request(method, path, body=payload, headers=request_headers)
        return connection.getresponse()

    def _register_and_verify(self, email):
        response = self._request("POST", "/api/register", {"email": email})
        data = json.loads(response.read().decode("utf-8"))
        token = data["verification_token"]
        response = self._request("POST", "/api/verify", {"token": token})
        self.assertEqual(response.status, 200)
        return data["user_id"]

    def test_login_sets_session_and_csrf_cookies(self):
        user_id = self._register_and_verify("api@example.com")
        self.stores.pii.update_user(user_id, role="analyst")
        response = self._request("POST", "/api/login", {"email": "api@example.com"})
        self.assertEqual(response.status, 200)
        cookies = response.getheaders()
        cookie_values = [value for key, value in cookies if key.lower() == "set-cookie"]
        self.assertTrue(any(cookie.startswith("session=") for cookie in cookie_values))
        self.assertTrue(any(cookie.startswith("csrf_token=") for cookie in cookie_values))

    def test_csrf_required_for_survey_creation(self):
        user_id = self._register_and_verify("survey@example.com")
        self.stores.pii.update_user(user_id, role="analyst")
        response = self._request("POST", "/api/login", {"email": "survey@example.com"})
        cookie_headers = [value for key, value in response.getheaders() if key.lower() == "set-cookie"]
        cookies = "; ".join(cookie.split(";", 1)[0] for cookie in cookie_headers)
        response = self._request(
            "POST",
            "/api/surveys",
            {"schema": {"questions": [{"type": "scale"}]}, "base_block_policy": "enabled"},
            headers={"Cookie": cookies},
        )
        self.assertEqual(response.status, 403)

        csrf_cookie = next(cookie for cookie in cookie_headers if cookie.startswith("csrf_token="))
        csrf_token = csrf_cookie.split(";", 1)[0].split("=", 1)[1]
        response = self._request(
            "POST",
            "/api/surveys",
            {"schema": {"questions": [{"type": "scale"}]}, "base_block_policy": "enabled"},
            headers={"Cookie": cookies, "X-CSRF-Token": csrf_token},
        )
        self.assertEqual(response.status, 200)


if __name__ == "__main__":
    unittest.main()
