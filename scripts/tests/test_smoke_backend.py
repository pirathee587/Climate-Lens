"""The infrastructure checker must reject false-green HTTP responses."""

import importlib.util
import io
import json
import threading
import unittest
from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

spec = importlib.util.spec_from_file_location(
    "smoke_backend", Path(__file__).resolve().parents[1] / "smoke_backend.py"
)
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


class SmokeTests(unittest.TestCase):
    def run_checker(self, *, mode="production", failure=None):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_OPTIONS(self):
                self.respond(preflight=True)

            def do_GET(self):
                self.respond()

            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", 0)))
                self.respond()

            def respond(self, preflight=False):
                request_id = str(uuid4())
                code, status = "NOT_FOUND", 404
                if preflight:
                    status = 200
                elif self.path == "/health":
                    status = 200
                elif self.path in ("/docs", "/openapi.json"):
                    status = 404 if mode == "production" else 200
                elif self.path == "/api/v1/analyses/not-a-uuid":
                    code, status = "INVALID_ARGUMENT", 422
                elif self.path in (
                    "/api/v1/variables",
                    "/api/v1/regions/presets",
                    "/api/v1/analyses",
                    "/api/v1/comparisons",
                ):
                    code, status = "DATASET_UNAVAILABLE", 503
                if failure == "fake_success" and self.path == "/api/v1/variables":
                    status = 200
                if failure == "docs" and self.path == "/docs":
                    status = 200
                payload = {
                    "error": {
                        "code": code,
                        "message": "Unavailable",
                        "details": {},
                        "request_id": request_id,
                    }
                }
                if self.path == "/health":
                    payload = {
                        "status": "ok",
                        "service": "terratrend-api",
                        "api_version": "v1",
                    }
                    if failure == "health":
                        payload["status"] = "wrong"
                if failure == "request_id" and "error" in payload:
                    payload["error"]["request_id"] = str(uuid4())
                self.send_response(status)
                self.send_header("X-Request-ID", request_id)
                self.send_header(
                    "Access-Control-Allow-Origin",
                    "wrong" if failure == "cors" else "http://localhost:5173",
                )
                self.send_header(
                    "Access-Control-Expose-Headers", "X-Request-ID, Content-Disposition"
                )
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode())

        with ThreadingHTTPServer(("127.0.0.1", 0), Handler) as server:
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with redirect_stdout(io.StringIO()):
                    smoke.check_backend(
                        f"http://127.0.0.1:{server.server_port}",
                        mode,
                        "http://localhost:5173",
                    )
            finally:
                server.shutdown()
                thread.join()

    def test_production_contract(self):
        self.run_checker()

    def test_development_contract(self):
        self.run_checker(mode="development")

    def test_reject_false_dataset_success(self):
        with self.assertRaises(smoke.SmokeFailure):
            self.run_checker(failure="fake_success")

    def test_reject_bad_health(self):
        with self.assertRaises(smoke.SmokeFailure):
            self.run_checker(failure="health")

    def test_reject_incorrect_cors(self):
        with self.assertRaises(smoke.SmokeFailure):
            self.run_checker(failure="cors")

    def test_reject_request_id_mismatch(self):
        with self.assertRaises(smoke.SmokeFailure):
            self.run_checker(failure="request_id")

    def test_reject_enabled_production_docs(self):
        with self.assertRaises(smoke.SmokeFailure):
            self.run_checker(failure="docs")
