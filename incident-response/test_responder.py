"""Unit tests for incident-response/responder.py — stdlib unittest only."""

import json
import os
import sys
import unittest
from http.server import HTTPServer
from threading import Thread
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# Make the incident-response directory importable
sys.path.insert(0, os.path.dirname(__file__))
import responder


SECRET = "test-secret-value"


class TestCheckAuth(unittest.TestCase):
    def test_correct_bearer(self):
        self.assertTrue(responder.check_auth(f"Bearer {SECRET}", SECRET))

    def test_missing_header(self):
        self.assertFalse(responder.check_auth(None, SECRET))

    def test_empty_header(self):
        self.assertFalse(responder.check_auth("", SECRET))

    def test_wrong_secret(self):
        self.assertFalse(responder.check_auth("Bearer wrong", SECRET))

    def test_wrong_scheme(self):
        self.assertFalse(responder.check_auth(f"Basic {SECRET}", SECRET))


class TestValidateAlertname(unittest.TestCase):
    def test_valid(self):
        self.assertTrue(responder.validate_alertname("SearchRunFailures"))

    def test_with_dashes_underscores(self):
        self.assertTrue(responder.validate_alertname("my_alert-1"))

    def test_traversal(self):
        self.assertFalse(responder.validate_alertname("../../etc"))

    def test_empty(self):
        self.assertFalse(responder.validate_alertname(""))

    def test_too_long(self):
        self.assertFalse(responder.validate_alertname("a" * 65))

    def test_spaces(self):
        self.assertFalse(responder.validate_alertname("bad name"))


class TestBuildAgentEnv(unittest.TestCase):
    def test_allowlist_only(self):
        # Inject extra env vars, verify they don't leak
        old = os.environ.copy()
        try:
            os.environ["DATABASE_URL"] = "postgres://leaked"
            os.environ["AWS_SECRET_ACCESS_KEY"] = "leaked"
            os.environ["ANTHROPIC_API_KEY"] = "sk-test"
            env = responder.build_agent_env()
            self.assertIn("PATH", env)
            self.assertIn("HOME", env)
            self.assertIn("ANTHROPIC_API_KEY", env)
            self.assertNotIn("DATABASE_URL", env)
            self.assertNotIn("AWS_SECRET_ACCESS_KEY", env)
        finally:
            os.environ.clear()
            os.environ.update(old)

    def test_no_api_key(self):
        old = os.environ.copy()
        try:
            os.environ.pop("ANTHROPIC_API_KEY", None)
            env = responder.build_agent_env()
            self.assertNotIn("ANTHROPIC_API_KEY", env)
            self.assertEqual(len(env), 2)  # PATH + HOME only
        finally:
            os.environ.clear()
            os.environ.update(old)


class TestFenceEvidence(unittest.TestCase):
    def test_delimiters_present(self):
        evidence = "some telemetry data\nmore lines"
        result = responder.fence_evidence(evidence)
        self.assertIn(responder.EVIDENCE_FENCE_START, result)
        self.assertIn(responder.EVIDENCE_FENCE_END, result)
        # Evidence between delimiters
        start_idx = result.index(responder.EVIDENCE_FENCE_START)
        end_idx = result.index(responder.EVIDENCE_FENCE_END)
        self.assertIn(evidence, result[start_idx:end_idx])


class TestBuildPrompt(unittest.TestCase):
    def test_evidence_fenced(self):
        template = "Alert fired.\n\n{evidence}\n\nIncident: {incident_id}"
        evidence = "error count: 5"
        prompt = responder.build_prompt(template, evidence, "20261017-test")
        self.assertIn(responder.EVIDENCE_FENCE_START, prompt)
        self.assertIn(responder.EVIDENCE_FENCE_END, prompt)
        self.assertIn("error count: 5", prompt)
        self.assertIn("20261017-test", prompt)


class TestHTTPEndpoint(unittest.TestCase):
    """Integration-style tests against a real HTTPServer."""

    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), responder.AlertHandler)
        cls.server.webhook_secret = SECRET
        cls.port = cls.server.server_address[1]
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def _url(self, path="/alerts"):
        return f"http://127.0.0.1:{self.port}{path}"

    def _post(self, data, headers=None):
        body = json.dumps(data).encode()
        req = Request(self._url(), data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)
        return urlopen(req)

    def test_401_without_auth(self):
        payload = {"alerts": [{"status": "firing", "labels": {"alertname": "Test"}}]}
        with self.assertRaises(HTTPError) as ctx:
            self._post(payload)
        self.assertEqual(ctx.exception.code, 401)

    def test_401_wrong_secret(self):
        payload = {"alerts": [{"status": "firing", "labels": {"alertname": "Test"}}]}
        with self.assertRaises(HTTPError) as ctx:
            self._post(payload, {"Authorization": "Bearer wrong"})
        self.assertEqual(ctx.exception.code, 401)

    def test_400_bad_alertname(self):
        payload = {"alerts": [{"status": "firing", "labels": {"alertname": "../../etc"}}]}
        with self.assertRaises(HTTPError) as ctx:
            self._post(payload, {"Authorization": f"Bearer {SECRET}"})
        self.assertEqual(ctx.exception.code, 400)

    def test_202_valid_request(self):
        # resolved status — won't spawn agent work but should be accepted
        payload = {"alerts": [{"status": "resolved", "labels": {"alertname": "OK"}}]}
        resp = self._post(payload, {"Authorization": f"Bearer {SECRET}"})
        self.assertEqual(resp.status, 202)


if __name__ == "__main__":
    unittest.main()
