from __future__ import annotations

from collections import Counter
from statistics import pstdev
from typing import Any

DIFFICULTY_MULTIPLIERS = {
    "easy": 0.8,
    "medium": 1.0,
    "hard": 1.2,
}

HINT_PENALTIES = {
    0: 1.0,
    1: 0.6,
    2: 0.2,
}

DIFFICULTY_ORDER = ["easy", "medium", "hard"]


def normalize_difficulty(value: str | None) -> str:
    if not value:
        return "medium"
    cleaned = value.strip().lower()
    return cleaned if cleaned in DIFFICULTY_MULTIPLIERS else "medium"


def shift_difficulty(current: str, direction: int) -> str:
    normalized = normalize_difficulty(current)
    index = DIFFICULTY_ORDER.index(normalized)
    next_index = max(0, min(len(DIFFICULTY_ORDER) - 1, index + direction))
    return DIFFICULTY_ORDER[next_index]


def pick_question_mix(target_difficulty: str, count: int) -> list[str]:
    normalized = normalize_difficulty(target_difficulty)
    presets = {
        "easy": ["easy", "easy", "easy", "medium", "medium"],
        "medium": ["easy", "medium", "medium", "medium", "hard"],
        "hard": ["medium", "medium", "hard", "hard", "hard"],
    }
    base_mix = presets[normalized]
    if count <= len(base_mix):
        return base_mix[:count]

    mix = list(base_mix)
    while len(mix) < count:
        mix.append(normalized)
    return mix


def calculate_session_result(
    *,
    questions: list[dict[str, Any]],
    submissions: list[dict[str, Any]],
    prior_avg_response_time: float,
    current_difficulty: str,
) -> dict[str, Any]:
    submission_map = {item["questionId"]: item for item in submissions if item.get("questionId")}
    reviews: list[dict[str, Any]] = []
    total_weighted_score = 0.0
    focus_skills: Counter[str] = Counter()

    for question in questions:
        submission = submission_map.get(question["id"], {})
        selected_index = submission.get("selectedIndex")
        hints_used = int(submission.get("hintsUsed", 0) or 0)
        response_time = float(submission.get("responseTimeSec", 0) or 0)
        correct_index = question["correct_index"]
        is_correct = selected_index == correct_index
        base = 1.0 if is_correct else 0.0
        difficulty = normalize_difficulty(question.get("difficulty"))
        hint_penalty = _hint_penalty(hints_used)
        weighted = base * DIFFICULTY_MULTIPLIERS[difficulty] * hint_penalty
        total_weighted_score += weighted

        if not is_correct:
            focus_skills[question.get("skill_tag", "Core practice")] += 1

        reviews.append(
            {
                "questionId": question["id"],
                "prompt": question["prompt"],
                "difficulty": difficulty,
                "skillTag": question.get("skill_tag", "Core practice"),
                "selectedIndex": selected_index,
                "selectedText": _safe_option(question, selected_index),
                "correctIndex": correct_index,
                "correctText": _safe_option(question, correct_index),
                "isCorrect": is_correct,
                "base": base,
                "difficultyMultiplier": DIFFICULTY_MULTIPLIERS[difficulty],
                "hintPenalty": hint_penalty,
                "weightedScore": round(weighted, 3),
                "hintsUsed": hints_used,
                "responseTimeSec": round(response_time, 1),
                "explanation": question.get("explanation", "Review the worked solution and try a similar example."),
                "hints": question.get("hints", []),
                "options": question.get("options", []),
            }
        )

    raw_score = calculate_weighted_average_score(
        total_weighted_score=total_weighted_score,
        n=len(questions),
    )
    question_count = max(1, len(questions))
    mastery_percent = min(100.0, raw_score * 100.0)
    accuracy_percent = (
        sum(1 for item in reviews if item["isCorrect"]) / question_count
    ) * 100.0
    average_response_time = round(
        sum(item["responseTimeSec"] for item in reviews) / question_count, 1
    )
    inconsistency_index = calculate_inconsistency_index(reviews)
    struggling = detect_struggle(
        reviews=reviews,
        prior_avg_response_time=prior_avg_response_time,
        average_response_time=average_response_time,
    )
    decision = decide_next_step(
        mastery_percent=mastery_percent,
        current_difficulty=current_difficulty,
        struggling=struggling,
        inconsistency_index=inconsistency_index,
    )
    prediction = predict_readiness(
        mastery_percent=mastery_percent,
        struggling=struggling,
        inconsistency_index=inconsistency_index,
    )

    summary = build_summary_sentence(
        mastery_percent=mastery_percent,
        accuracy_percent=accuracy_percent,
        struggling=struggling,
        inconsistency_index=inconsistency_index,
        decision=decision,
    )

    return {
        "rawScore": round(raw_score, 3),
        "masteryPercent": round(mastery_percent, 1),
        "accuracyPercent": round(accuracy_percent, 1),
        "averageResponseTimeSec": average_response_time,
        "priorAverageResponseTimeSec": round(prior_avg_response_time, 1),
        "struggling": struggling,
        "inconsistencyIndex": round(inconsistency_index, 3),
        "suspicionLevel": classify_suspicion(inconsistency_index),
        "decision": decision,
        "prediction": prediction,
        "focusSkills": [skill for skill, _ in focus_skills.most_common(3)],
        "questionReviews": reviews,
        "summary": summary,
    }


def calculate_weighted_average_score(*, total_weighted_score: float, n: int) -> float:
    """Apply Score = (1/n) * sum(Base * Difficulty * HintPenalty)."""
    safe_n = max(1, n)
    return (1 / safe_n) * total_weighted_score


def calculate_inconsistency_index(reviews: list[dict[str, Any]]) -> float:
    pairs = 0
    inversions = 0
    for left_index, left in enumerate(reviews):
        for right in reviews[left_index + 1 :]:
            left_rank = _difficulty_rank(left["difficulty"])
            right_rank = _difficulty_rank(right["difficulty"])
            if left_rank == right_rank:
                continue
            easier, harder = (left, right) if left_rank < right_rank else (right, left)
            pairs += 1
            if (not easier["isCorrect"]) and harder["isCorrect"]:
                inversions += 1

    inversion_ratio = inversions / pairs if pairs else 0.0
    times = [item["responseTimeSec"] for item in reviews if item["responseTimeSec"] > 0]
    volatility = 0.0
    if len(times) >= 2:
        average_time = sum(times) / len(times)
        volatility = min(1.0, pstdev(times) / max(average_time, 1.0))

    return min(1.0, (0.7 * inversion_ratio) + (0.3 * volatility))


def detect_struggle(
    *,
    reviews: list[dict[str, Any]],
    prior_avg_response_time: float,
    average_response_time: float,
) -> bool:
    if prior_avg_response_time > 0 and average_response_time > (prior_avg_response_time * 2):
        return True

    if prior_avg_response_time > 0:
        for review in reviews:
            if review["responseTimeSec"] > (prior_avg_response_time * 2):
                return True

    accuracy = sum(1 for item in reviews if item["isCorrect"]) / max(1, len(reviews))
    return accuracy < 0.4 and average_response_time >= 70


def decide_next_step(
    *,
    mastery_percent: float,
    current_difficulty: str,
    struggling: bool,
    inconsistency_index: float,
) -> dict[str, Any]:
    normalized = normalize_difficulty(current_difficulty)

    if mastery_percent > 85 and not struggling and inconsistency_index < 0.4:
        next_difficulty = shift_difficulty(normalized, 1)
        recommendation = "Advance to the next topic focus" if next_difficulty == "hard" else "Increase difficulty for the next session"
        return {
            "mode": "advance",
            "nextDifficulty": next_difficulty,
            "recommendation": recommendation,
            "rationale": "Strong mastery with steady response patterns signals readiness for a bigger challenge.",
        }

    if mastery_percent < 50 or struggling:
        next_difficulty = shift_difficulty(normalized, -1)
        return {
            "mode": "review",
            "nextDifficulty": next_difficulty,
            "recommendation": "Switch to review mode and reinforce the current skill cluster",
            "rationale": "Accuracy or response timing suggests the learner needs consolidation before advancing.",
        }

    return {
        "mode": "stabilize",
        "nextDifficulty": normalized,
        "recommendation": "Stay at the current difficulty and build consistency",
        "rationale": "Performance is developing, but another round at this level will create a stronger base.",
    }


def predict_readiness(
    *,
    mastery_percent: float,
    struggling: bool,
    inconsistency_index: float,
) -> dict[str, Any]:
    if struggling:
        return {
            "band": "Watchlist",
            "headline": "The learner may be struggling under current pacing.",
            "detail": "Expect better outcomes after a slower review session with more guided hints.",
        }

    if mastery_percent >= 85 and inconsistency_index < 0.3:
        return {
            "band": "Ready",
            "headline": "The learner is likely ready for harder problems or the next topic.",
            "detail": "Stable accuracy and response timing suggest strong concept retention.",
        }

    if inconsistency_index >= 0.45:
        return {
            "band": "Variable",
            "headline": "Performance looks inconsistent and may fluctuate from session to session.",
            "detail": "The pattern of missing easier questions while solving harder ones should be monitored.",
        }

    return {
        "band": "Building",
        "headline": "The learner is building mastery but still benefits from repetition.",
        "detail": "Another set at the same level should sharpen accuracy and confidence.",
    }


def classify_suspicion(inconsistency_index: float) -> str:
    if inconsistency_index >= 0.6:
        return "High"
    if inconsistency_index >= 0.35:
        return "Moderate"
    return "Low"


def update_progress_snapshot(
    *,
    previous_progress: dict[str, Any],
    session_result: dict[str, Any],
    education_level: str,
) -> dict[str, Any]:
    previous_mastery = float(previous_progress.get("mastery", 0.0) or 0.0)
    previous_avg_time = float(previous_progress.get("avg_response_time", 0.0) or 0.0)
    sessions_completed = int(previous_progress.get("sessions_completed", 0) or 0)

    if sessions_completed <= 0:
        blended_mastery = session_result["masteryPercent"]
        blended_avg_time = session_result["averageResponseTimeSec"]
    else:
        blended_mastery = (previous_mastery * 0.65) + (session_result["masteryPercent"] * 0.35)
        blended_avg_time = (previous_avg_time * 0.7) + (session_result["averageResponseTimeSec"] * 0.3)

    return {
        "education_level": education_level,
        "current_difficulty": session_result["decision"]["nextDifficulty"],
        "mastery": round(blended_mastery, 1),
        "avg_response_time": round(blended_avg_time, 1),
        "sessions_completed": sessions_completed + 1,
        "last_decision": session_result["decision"]["mode"],
        "struggling": 1 if session_result["struggling"] else 0,
        "inconsistency_score": session_result["inconsistencyIndex"],
        "predicted_band": session_result["prediction"]["band"],
    }


def build_summary_sentence(
    *,
    mastery_percent: float,
    accuracy_percent: float,
    struggling: bool,
    inconsistency_index: float,
    decision: dict[str, Any],
) -> str:
    if struggling:
        return (
            f"Mastery landed at {mastery_percent:.1f}% with response timing that suggests the learner is under strain. "
            f"The best next move is to {decision['recommendation'].lower()}."
        )

    if inconsistency_index >= 0.45:
        return (
            f"Mastery reached {mastery_percent:.1f}% with {accuracy_percent:.1f}% raw accuracy, but the answer pattern was inconsistent. "
            f"The system recommends {decision['recommendation'].lower()}."
        )

    return (
        f"Mastery reached {mastery_percent:.1f}% with {accuracy_percent:.1f}% raw accuracy. "
        f"The adaptive engine recommends {decision['recommendation'].lower()}."
    )


def _difficulty_rank(value: str) -> int:
    return DIFFICULTY_ORDER.index(normalize_difficulty(value))


def _hint_penalty(hints_used: int) -> float:
    if hints_used <= 0:
        return HINT_PENALTIES[0]
    if hints_used == 1:
        return HINT_PENALTIES[1]
    return HINT_PENALTIES[2]


def _safe_option(question: dict[str, Any], index: int | None) -> str | None:
    if index is None:
        return None
    options = question.get("options", [])
    if 0 <= index < len(options):
        return options[index]
    return None
