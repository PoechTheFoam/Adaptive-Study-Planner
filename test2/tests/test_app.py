from __future__ import annotations

import json
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from app.config import AppConfig
from app.server import Application


class AppSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name)
        self.static_dir = self.base_dir / "static"
        self.static_dir.mkdir()
        (self.static_dir / "index.html").write_text("<html><body>ok</body></html>", encoding="utf-8")

        self.app = Application(
            AppConfig(
                base_dir=self.base_dir,
                static_dir=self.static_dir,
                database_path=self.base_dir / "test.db",
                host="127.0.0.1",
                port=8080,
                ai_provider="gemini",
                gemini_api_key="",
                gemini_model="gemini-2.5-flash",
            )
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_full_session_flow(self) -> None:
        meta = self.call_json("GET", "/api/meta")
        self.assertIn("topics", meta)

        snapshot = self.call_json(
            "POST",
            "/api/profile/register",
            {
                "name": "Minh",
                "topic": "algebra",
                "educationLevel": "High School",
            },
        )
        profile_id = snapshot["profile"]["id"]

        session = self.call_json(
            "POST",
            "/api/session/start",
            {
                "profileId": profile_id,
                "topic": "algebra",
                "educationLevel": "High School",
                "questionCount": 5,
            },
        )
        session_id = session["sessionId"]
        stored_session = self.app.storage.get_session(session_id)
        self.assertIsNotNone(stored_session)

        answers = [
            {
                "questionId": question["id"],
                "selectedIndex": question["correct_index"],
                "hintsUsed": 0,
                "responseTimeSec": 18.0,
            }
            for question in stored_session["questions"]
        ]

        result = self.call_json(
            "POST",
            "/api/session/submit",
            {
                "sessionId": session_id,
                "answers": answers,
            },
        )

        self.assertIn("evaluation", result)
        self.assertGreaterEqual(result["evaluation"]["masteryPercent"], 80)
        self.assertIn("profileSnapshot", result)

    def call_json(self, method: str, path: str, payload: dict | None = None) -> dict:
        body = json.dumps(payload).encode("utf-8") if payload is not None else b""
        captured: dict[str, object] = {}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            captured["status"] = status
            captured["headers"] = headers

        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "CONTENT_LENGTH": str(len(body)),
            "CONTENT_TYPE": "application/json",
            "wsgi.input": BytesIO(body),
            "SERVER_NAME": "127.0.0.1",
            "SERVER_PORT": "8080",
            "SERVER_PROTOCOL": "HTTP/1.1",
        }
        response_body = b"".join(self.app(environ, start_response))
        status = str(captured["status"])
        self.assertTrue(status.startswith(("200", "201")), msg=response_body.decode("utf-8"))
        return json.loads(response_body.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
