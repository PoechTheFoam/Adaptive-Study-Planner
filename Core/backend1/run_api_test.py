import json
import os
import sys

from fastapi.testclient import TestClient

os.environ["GEMINI_API_KEY"] = ""


def require_ok(response, name):
    payload = response.json()
    print(name, response.status_code, json.dumps(payload, ensure_ascii=True))
    if response.status_code >= 400:
        raise SystemExit(1)
    return payload


def main():
    from main import app

    client = TestClient(app)

    root_response = client.get("/")
    print(
        "frontend_root",
        root_response.status_code,
        root_response.headers.get("content-type"),
    )
    if (
        root_response.status_code >= 400
        or "SciMath Adaptive Coach" not in root_response.text
    ):
        raise SystemExit(1)

    require_ok(client.get("/health"), "health")

    user = require_ok(
        client.post(
            "/user/create",
            json={
                "name": "WebTestUser",
                "skill_level": "beginner",
                "goal": "mastery",
                "initial_topic": "algebra",
            },
        ),
        "create_user",
    )

    question = require_ok(
        client.post("/get_question", json={"user_id": user["user_id"]}),
        "get_question",
    )

    require_ok(
        client.post(
            "/submit_answer",
            json={
                "user_id": user["user_id"],
                "exercise_id": question["exercise_id"],
                "user_answer": "42",
                "response_time": 12.3,
                "hints_used": 0,
            },
        ),
        "submit_answer",
    )

    require_ok(
        client.post("/next_action", params={"user_id": user["user_id"]}),
        "next_action",
    )
    require_ok(
        client.get("/user/profile", params={"user_id": user["user_id"]}),
        "user_profile",
    )
    require_ok(
        client.get("/user/progress", params={"user_id": user["user_id"]}),
        "user_progress",
    )
    print("api_smoke_test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
