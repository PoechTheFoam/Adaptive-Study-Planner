from __future__ import annotations

import json
import mimetypes
import posixpath
from http import HTTPStatus
from typing import Any
from wsgiref.simple_server import make_server

from app.adaptive import calculate_session_result, update_progress_snapshot
from app.config import AppConfig, load_config
from app.services.content_engine import ContentEngine
from app.services.gemini_client import GeminiClient
from app.storage import Storage


class Application:
    def __init__(self, config: AppConfig):
        self.config = config
        self.storage = Storage(config.database_path)
        self.storage.initialize()
        self.content_engine = ContentEngine(
            gemini_client=GeminiClient(
                api_key=config.gemini_api_key,
                model=config.gemini_model,
            )
        )

    def __call__(self, environ: dict[str, Any], start_response: Any) -> list[bytes]:
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "/")

        try:
            if path.startswith("/api/"):
                return self._handle_api(method, path, environ, start_response)
            return self._serve_static(path, start_response)
        except KeyError as exc:
            return self._json_response(start_response, HTTPStatus.NOT_FOUND, {"error": str(exc)})
        except ValueError as exc:
            return self._json_response(start_response, HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except Exception as exc:
            return self._json_response(
                start_response,
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "Unexpected server error", "detail": str(exc)},
            )

    def _handle_api(
        self,
        method: str,
        path: str,
        environ: dict[str, Any],
        start_response: Any,
    ) -> list[bytes]:
        if method == "GET" and path == "/api/health":
            return self._json_response(
                start_response,
                HTTPStatus.OK,
                {
                    "status": "ok",
                    "databasePath": str(self.config.database_path),
                    "provider": self.config.ai_provider,
                    "geminiEnabled": bool(self.config.gemini_api_key),
                    "geminiModel": self.config.gemini_model,
                },
            )

        if method == "GET" and path == "/api/meta":
            return self._json_response(start_response, HTTPStatus.OK, self.content_engine.metadata())

        if method == "POST" and path == "/api/profile/register":
            payload = self._read_json(environ)
            name = str(payload.get("name") or "").strip()
            topic = str(payload.get("topic") or "").strip().lower()
            education_level = str(payload.get("educationLevel") or "").strip()

            if not name:
                raise ValueError("Name is required.")
            if not topic:
                raise ValueError("Topic is required.")
            if not education_level:
                raise ValueError("Education level is required.")

            snapshot = self.storage.create_profile(
                name=name,
                education_level=education_level,
                topic=topic,
            )
            return self._json_response(start_response, HTTPStatus.CREATED, snapshot)

        if method == "GET" and path.startswith("/api/profile/"):
            profile_id = path.rsplit("/", 1)[-1]
            snapshot = self.storage.get_profile_snapshot(profile_id)
            if snapshot is None:
                raise KeyError("Profile not found")
            return self._json_response(start_response, HTTPStatus.OK, snapshot)

        if method == "POST" and path == "/api/session/start":
            payload = self._read_json(environ)
            profile_id = str(payload.get("profileId") or "").strip()
            topic = str(payload.get("topic") or "").strip().lower()
            education_level = str(payload.get("educationLevel") or "").strip()
            question_count = int(payload.get("questionCount", 5) or 5)

            if not profile_id:
                raise ValueError("Profile ID is required.")
            if not topic:
                raise ValueError("Topic is required.")
            if not education_level:
                raise ValueError("Education level is required.")

            snapshot = self.storage.ensure_profile_topic(
                profile_id=profile_id,
                topic=topic,
                education_level=education_level,
            )
            progress = self.storage.get_topic_progress(profile_id=profile_id, topic=topic)
            if progress is None:
                raise KeyError("Topic progress not found")

            quiz = self.content_engine.generate_quiz(
                context={
                    "name": snapshot["profile"]["name"],
                    "topic": topic,
                    "educationLevel": education_level,
                    "targetDifficulty": progress["currentDifficulty"],
                    "mastery": progress["mastery"],
                    "avgResponseTime": progress["avgResponseTime"],
                    "sessionsCompleted": progress["sessionsCompleted"],
                    "questionCount": question_count,
                }
            )
            session = self.storage.create_session(
                profile_id=profile_id,
                topic=topic,
                education_level=education_level,
                requested_difficulty=progress["currentDifficulty"],
                delivered_difficulty=progress["currentDifficulty"],
                content_source=quiz["source"],
                questions=quiz["questions"],
            )
            public_questions = [self._public_question(question) for question in quiz["questions"]]
            return self._json_response(
                start_response,
                HTTPStatus.OK,
                {
                    "sessionId": session["id"],
                    "quizTitle": quiz["quizTitle"],
                    "introMessage": quiz["introMessage"],
                    "contentSource": quiz["source"],
                    "targetDifficulty": progress["currentDifficulty"],
                    "questions": public_questions,
                    "topicProgress": progress,
                },
            )

        if method == "POST" and path == "/api/session/submit":
            payload = self._read_json(environ)
            session_id = str(payload.get("sessionId") or "").strip()
            submissions = payload.get("answers") or []
            if not session_id:
                raise ValueError("Session ID is required.")
            if not isinstance(submissions, list) or not submissions:
                raise ValueError("Answers are required.")

            session = self.storage.get_session(session_id)
            if session is None:
                raise KeyError("Session not found")

            progress = self.storage.get_topic_progress(
                profile_id=session["profile_id"],
                topic=session["topic"],
            )
            if progress is None:
                raise KeyError("Topic progress not found")

            result = calculate_session_result(
                questions=session["questions"],
                submissions=submissions,
                prior_avg_response_time=float(progress["avgResponseTime"] or 0.0),
                current_difficulty=progress["currentDifficulty"],
            )
            updated_progress = update_progress_snapshot(
                previous_progress={
                    "mastery": progress["mastery"],
                    "avg_response_time": progress["avgResponseTime"],
                    "sessions_completed": progress["sessionsCompleted"],
                },
                session_result=result,
                education_level=session["education_level"],
            )
            self.storage.complete_session(
                session_id=session_id,
                submissions=submissions,
                result=result,
            )
            self.storage.save_topic_progress(
                profile_id=session["profile_id"],
                topic=session["topic"],
                values=updated_progress,
            )
            snapshot = self.storage.get_profile_snapshot(session["profile_id"])
            if snapshot is None:
                raise KeyError("Profile not found")
            study_plan = self.content_engine.build_study_plan(
                learner_name=snapshot["profile"]["name"],
                topic=session["topic"],
                education_level=session["education_level"],
                evaluation=result,
            )

            return self._json_response(
                start_response,
                HTTPStatus.OK,
                {
                    "sessionId": session_id,
                    "evaluation": result,
                    "studyPlan": study_plan,
                    "profileSnapshot": snapshot,
                },
            )

        return self._json_response(
            start_response,
            HTTPStatus.NOT_FOUND,
            {"error": "Route not found"},
        )

    def _serve_static(self, path: str, start_response: Any) -> list[bytes]:
        relative_path = path if path != "/" else "/index.html"
        relative_path = posixpath.normpath(relative_path).lstrip("/")
        file_path = (self.config.static_dir / relative_path).resolve()

        if not str(file_path).startswith(str(self.config.static_dir.resolve())):
            return self._json_response(start_response, HTTPStatus.FORBIDDEN, {"error": "Forbidden"})

        if file_path.is_dir():
            file_path = file_path / "index.html"
        if not file_path.exists():
            file_path = self.config.static_dir / "index.html"

        content = file_path.read_bytes()
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        start_response(
            f"{HTTPStatus.OK.value} {HTTPStatus.OK.phrase}",
            [
                ("Content-Type", content_type),
                ("Content-Length", str(len(content))),
                ("Cache-Control", "no-store"),
            ],
        )
        return [content]

    def _read_json(self, environ: dict[str, Any]) -> dict[str, Any]:
        try:
            content_length = int(environ.get("CONTENT_LENGTH") or "0")
        except ValueError:
            content_length = 0
        raw = environ["wsgi.input"].read(content_length) if content_length else b"{}"
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _json_response(self, start_response: Any, status: HTTPStatus, payload: dict[str, Any]) -> list[bytes]:
        body = json.dumps(payload).encode("utf-8")
        start_response(
            f"{status.value} {status.phrase}",
            [
                ("Content-Type", "application/json; charset=utf-8"),
                ("Content-Length", str(len(body))),
                ("Cache-Control", "no-store"),
            ],
        )
        return [body]

    def _public_question(self, question: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": question["id"],
            "prompt": question["prompt"],
            "difficulty": question["difficulty"],
            "skillTag": question.get("skill_tag", "Core practice"),
            "options": question["options"],
            "hints": question.get("hints", []),
            "estimatedTimeSec": question.get("estimated_time_sec", 60),
        }


def create_app() -> Application:
    return Application(load_config())


def run_server() -> None:
    config = load_config()
    app = Application(config)
    metadata = app.content_engine.metadata()
    education_levels = ", ".join(metadata.get("educationLevels", []))
    with make_server(config.host, config.port, app) as server:
        print(f"Serving Adaptive AI Partner on http://{config.host}:{config.port}")
        print(f"Active education levels: {education_levels}")
        print(
            "AI mode: "
            f"{metadata.get('ai', {}).get('provider', 'unknown')} "
            f"({metadata.get('ai', {}).get('geminiModel', 'n/a')})"
        )
        server.serve_forever()
