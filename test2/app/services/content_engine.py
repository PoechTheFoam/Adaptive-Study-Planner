from __future__ import annotations

import json
from typing import Any

from app.adaptive import normalize_difficulty
from app.services.gemini_client import GeminiClient
from app.services.local_question_bank import LocalMathGenerator

TOPICS = [
    {"id": "algebra", "label": "Algebra", "description": "Equations, patterns, and symbolic reasoning"},
    {"id": "calculus", "label": "Calculus", "description": "Rates of change, derivatives, and accumulation"},
    {"id": "geometry", "label": "Geometry", "description": "Shapes, area, angles, and spatial reasoning"},
    {"id": "statistics", "label": "Statistics", "description": "Data, averages, and probability"},
    {"id": "trigonometry", "label": "Trigonometry", "description": "Triangles, identities, and circular reasoning"},
    {"id": "arithmetic", "label": "Arithmetic", "description": "Number sense, fluency, and operations"},
]

EDUCATION_LEVELS = [
    "Middle School",
    "High School",
    "College",
]

TOPIC_LABELS = {topic["id"]: topic["label"] for topic in TOPICS}


class ContentEngine:
    def __init__(self, *, gemini_client: GeminiClient):
        self.gemini_client = gemini_client
        self.local_generator = LocalMathGenerator()

    def metadata(self) -> dict[str, Any]:
        return {
            "topics": TOPICS,
            "educationLevels": EDUCATION_LEVELS,
            "difficultyScale": ["easy", "medium", "hard"],
            "ai": {
                "provider": "gemini" if self.gemini_client.enabled else "local-fallback",
                "geminiEnabled": self.gemini_client.enabled,
                "geminiModel": self.gemini_client.model,
            },
        }

    def generate_quiz(self, *, context: dict[str, Any]) -> dict[str, Any]:
        topic = str(context.get("topic", "algebra")).strip().lower()
        education_level = str(context.get("educationLevel", "High School")).strip()
        target_difficulty = normalize_difficulty(context.get("targetDifficulty"))
        question_count = int(context.get("questionCount", 5) or 5)

        if self.gemini_client.enabled:
            try:
                gemini_quiz = self._generate_with_gemini(
                    topic=topic,
                    education_level=education_level,
                    target_difficulty=target_difficulty,
                    question_count=question_count,
                    context=context,
                )
                gemini_quiz["source"] = f"gemini:{self.gemini_client.model}"
                return gemini_quiz
            except Exception:
                pass

        return self.local_generator.generate_quiz(
            topic=topic,
            education_level=education_level,
            target_difficulty=target_difficulty,
            question_count=question_count,
        )

    def build_study_plan(
        self,
        *,
        learner_name: str,
        topic: str,
        education_level: str,
        evaluation: dict[str, Any],
    ) -> dict[str, Any]:
        if self.gemini_client.enabled:
            try:
                plan = self._build_study_plan_with_gemini(
                    learner_name=learner_name,
                    topic=topic,
                    education_level=education_level,
                    evaluation=evaluation,
                )
                plan["provider"] = f"gemini:{self.gemini_client.model}"
                return plan
            except Exception:
                pass

        plan = self._build_local_study_plan(
            learner_name=learner_name,
            topic=topic,
            education_level=education_level,
            evaluation=evaluation,
        )
        plan["provider"] = "local-fallback"
        return plan

    def _generate_with_gemini(
        self,
        *,
        topic: str,
        education_level: str,
        target_difficulty: str,
        question_count: int,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        learner_summary = {
            "name": context.get("name"),
            "mastery": context.get("mastery"),
            "avgResponseTime": context.get("avgResponseTime"),
            "sessionsCompleted": context.get("sessionsCompleted"),
        }
        prompt = f"""
You are generating a math quiz for an adaptive tutoring system.

Return only valid JSON with this exact structure:
{{
  "quizTitle": "short title",
  "introMessage": "one concise sentence",
  "questions": [
    {{
      "id": "q1",
      "prompt": "question text",
      "difficulty": "easy|medium|hard",
      "skill_tag": "skill name",
      "options": ["A", "B", "C", "D"],
      "correct_index": 0,
      "hints": ["hint one", "hint two"],
      "explanation": "2-4 sentence explanation",
      "estimated_time_sec": 60
    }}
  ]
}}

Constraints:
- Topic: {topic}
- Education level: {education_level}
- Target difficulty: {target_difficulty}
- Question count: {question_count}
- Exactly 4 options per question.
- A single unambiguous correct option.
- Keep explanations student-friendly.
- Learner context: {json.dumps(learner_summary)}
"""
        payload = self.gemini_client.generate_quiz_payload(prompt)
        return self._validate_quiz_payload(payload, expected_count=question_count)

    def _build_study_plan_with_gemini(
        self,
        *,
        learner_name: str,
        topic: str,
        education_level: str,
        evaluation: dict[str, Any],
    ) -> dict[str, Any]:
        prompt = f"""
You are an encouraging math tutor building a short personalized study plan.

Return only valid JSON with this exact structure:
{{
  "headline": "short title",
  "summary": "2 sentence summary",
  "timeMinutes": 15,
  "prioritySkills": ["skill 1", "skill 2", "skill 3"],
  "steps": [
    {{
      "title": "short step title",
      "durationMin": 5,
      "detail": "one concise instruction"
    }}
  ],
  "practicePrompt": "one short practice task",
  "encouragement": "one supportive sentence"
}}

Constraints:
- Keep it practical for a single 15-minute session.
- Tailor the plan to the student's weak areas and recommended next move.
- Give exactly 3 steps.
- Keep each detail concise and actionable.

Student: {learner_name}
Topic: {topic}
Education level: {education_level}
Performance data: {json.dumps({
    "masteryPercent": evaluation.get("masteryPercent"),
    "accuracyPercent": evaluation.get("accuracyPercent"),
    "averageResponseTimeSec": evaluation.get("averageResponseTimeSec"),
    "focusSkills": evaluation.get("focusSkills", []),
    "decision": evaluation.get("decision", {}),
    "prediction": evaluation.get("prediction", {}),
    "summary": evaluation.get("summary", ""),
})}
"""
        payload = self.gemini_client.generate_json_payload(prompt)
        return self._validate_study_plan_payload(payload)

    def _validate_quiz_payload(self, payload: dict[str, Any], *, expected_count: int) -> dict[str, Any]:
        quiz_title = str(payload.get("quizTitle") or "Adaptive Math Quiz")
        intro_message = str(payload.get("introMessage") or "A personalized set generated for the learner.")
        questions = payload.get("questions")
        if not isinstance(questions, list) or not questions:
            raise ValueError("Quiz payload did not include questions.")

        validated_questions = []
        for index, item in enumerate(questions[:expected_count], start=1):
            options = item.get("options", [])
            if not isinstance(options, list) or len(options) != 4:
                raise ValueError("Each question must have exactly 4 options.")

            correct_index = int(item.get("correct_index", 0))
            if correct_index < 0 or correct_index > 3:
                raise ValueError("Correct index out of range.")

            validated_questions.append(
                {
                    "id": str(item.get("id") or f"q{index}"),
                    "prompt": str(item.get("prompt") or "Solve the problem."),
                    "difficulty": normalize_difficulty(str(item.get("difficulty") or "medium")),
                    "skill_tag": str(item.get("skill_tag") or "Core practice"),
                    "options": [str(option) for option in options],
                    "correct_index": correct_index,
                    "hints": [str(hint) for hint in (item.get("hints") or [])][:2],
                    "explanation": str(item.get("explanation") or "Review the worked example and try again."),
                    "estimated_time_sec": int(item.get("estimated_time_sec", 60) or 60),
                }
            )

        if not validated_questions:
            raise ValueError("No valid questions returned.")

        return {
            "quizTitle": quiz_title,
            "introMessage": intro_message,
            "questions": validated_questions,
        }

    def _validate_study_plan_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        priority_skills = payload.get("prioritySkills") or []
        if not isinstance(priority_skills, list):
            priority_skills = []

        steps = payload.get("steps") or []
        if not isinstance(steps, list):
            steps = []

        validated_steps = []
        for item in steps[:3]:
            validated_steps.append(
                {
                    "title": str(item.get("title") or "Study step"),
                    "durationMin": int(item.get("durationMin", 5) or 5),
                    "detail": str(item.get("detail") or "Review the concept and solve one fresh example."),
                }
            )

        if not validated_steps:
            raise ValueError("Study plan did not include steps.")

        return {
            "headline": str(payload.get("headline") or "Your next 15-minute study plan"),
            "summary": str(payload.get("summary") or "This short review will reinforce the most important skill from the session."),
            "timeMinutes": int(payload.get("timeMinutes", 15) or 15),
            "prioritySkills": [str(skill) for skill in priority_skills[:3]],
            "steps": validated_steps,
            "practicePrompt": str(payload.get("practicePrompt") or "Solve one more problem at the same level without using hints."),
            "encouragement": str(payload.get("encouragement") or "A short focused review right now will make the next session feel easier."),
        }

    def _build_local_study_plan(
        self,
        *,
        learner_name: str,
        topic: str,
        education_level: str,
        evaluation: dict[str, Any],
    ) -> dict[str, Any]:
        focus_skills = [str(skill) for skill in (evaluation.get("focusSkills") or [])]
        topic_label = TOPIC_LABELS.get(topic, topic.title())
        primary_skill = focus_skills[0] if focus_skills else f"{topic_label} core practice"
        secondary_skill = focus_skills[1] if len(focus_skills) > 1 else f"{topic_label} accuracy"
        next_difficulty = str(evaluation.get("decision", {}).get("nextDifficulty") or "medium")
        mastery = float(evaluation.get("masteryPercent", 0.0) or 0.0)

        if mastery >= 80:
            summary = f"{learner_name} is close to strong command in {topic_label}. This plan keeps momentum while tightening small gaps."
        elif mastery >= 55:
            summary = f"{learner_name} is building a good base in {topic_label}. This plan focuses on consistency before the next quiz."
        else:
            summary = f"{learner_name} needs a shorter recovery block in {topic_label}. This plan rebuilds the foundation first."

        return {
            "headline": f"{topic_label} 15-minute recovery plan",
            "summary": summary,
            "timeMinutes": 15,
            "prioritySkills": [primary_skill, secondary_skill, f"{next_difficulty.title()}-level confidence"],
            "steps": [
                {
                    "title": "Warm up the concept",
                    "durationMin": 4,
                    "detail": f"Review one solved example focused on {primary_skill} and say the rule out loud.",
                },
                {
                    "title": "Guided practice",
                    "durationMin": 6,
                    "detail": f"Solve 2 questions on {primary_skill} and {secondary_skill}, using hints only after a full attempt.",
                },
                {
                    "title": "Independent check",
                    "durationMin": 5,
                    "detail": f"Finish with 1 fresh {topic_label.lower()} question at {next_difficulty} difficulty with no hints.",
                },
            ],
            "practicePrompt": f"Create one extra {topic_label.lower()} problem about {primary_skill} and solve it step by step.",
            "encouragement": "Short, focused review beats long unfocused study. One strong 15-minute block will help the next session a lot.",
        }
