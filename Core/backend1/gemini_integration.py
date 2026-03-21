"""
Gemini API integration for the Adaptive Learning Platform.

Handles:
- Question generation
- Hint generation
- Explanation generation
"""
import json
from typing import Dict, Optional

import google.generativeai as genai

from config import GEMINI_API_KEY, GEMINI_CONFIG
from models import DifficultyLevel


if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class GeminiIntegration:
    """Integration with Google's Gemini API for content generation."""

    def __init__(self):
        self.model_name = GEMINI_CONFIG["model"]
        self.temperature = GEMINI_CONFIG["temperature"]
        self.max_tokens = GEMINI_CONFIG["max_output_tokens"]
        self.api_key = GEMINI_API_KEY

        if not self.api_key:
            print("WARNING: Gemini API key not configured.")

    def generate_question(
        self,
        topic: str,
        difficulty: DifficultyLevel,
        skill_level: str,
        goal: str,
    ) -> Optional[Dict]:
        """
        Generate a question using Gemini API.

        Returns a fallback demo question when the API key is unavailable.
        """
        if not self.api_key:
            print("WARNING: Falling back to demo question generation.")
            return self._get_dummy_question(topic, difficulty)

        try:
            prompt = self._build_question_prompt(
                topic, difficulty, skill_level, goal
            )

            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                ),
            )

            return self._parse_question_response(response.text)
        except Exception as e:
            print(f"Error generating question: {e}")
            return self._get_dummy_question(topic, difficulty)

    def generate_hint(
        self,
        question: str,
        topic: str,
        hint_number: int = 1,
    ) -> Optional[str]:
        """Generate a hint for a question using Gemini API."""
        if not self.api_key:
            return self._get_dummy_hint(question, hint_number)

        try:
            prompt = self._build_hint_prompt(question, topic, hint_number)

            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=500,
                ),
            )

            return response.text.strip()
        except Exception as e:
            print(f"Error generating hint: {e}")
            return self._get_dummy_hint(question, hint_number)

    def generate_explanation(
        self,
        question: str,
        correct_answer: str,
        user_answer: str = None,
    ) -> Optional[str]:
        """Generate an explanation for why an answer is correct."""
        if not self.api_key:
            return f"The correct answer is '{correct_answer}'. Please review the concept."

        try:
            prompt = self._build_explanation_prompt(
                question, correct_answer, user_answer
            )

            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=800,
                ),
            )

            return response.text.strip()
        except Exception as e:
            print(f"Error generating explanation: {e}")
            return f"The correct answer is '{correct_answer}'."

    def _build_question_prompt(
        self,
        topic: str,
        difficulty: DifficultyLevel,
        skill_level: str,
        goal: str,
    ) -> str:
        """Build the prompt for question generation."""
        difficulty_description = {
            "easy": "basic concept, simple calculation",
            "medium": "requires multiple steps, moderate difficulty",
            "hard": "advanced, requires problem-solving skills",
        }

        prompt = f"""Generate a {difficulty.value} math question about "{topic}" for a {skill_level} student.
Goal: {goal}

Requirements:
1. Create a clear, single math question
2. The answer should be a specific numerical value or brief statement
3. Question should be appropriate for the {goal} learning goal
4. Difficulty: {difficulty_description.get(difficulty.value, difficulty.value)}

Format your response as JSON with these exact keys:
{{
    "question": "The math problem here",
    "answer": "The correct answer (numerical or brief)",
    "explanation": "Why this is correct, step-by-step",
    "hints": [
        "First hint - point toward approach",
        "Second hint - more specific guidance"
    ]
}}

Only return valid JSON, no other text."""

        return prompt

    def _build_hint_prompt(
        self,
        question: str,
        topic: str,
        hint_number: int,
    ) -> str:
        """Build the prompt for hint generation."""
        if hint_number == 1:
            hint_type = "a general approach or concept to consider"
        else:
            hint_type = "a more specific clue or next step"

        return f"""For this {topic} question, provide {hint_type}:

Question: {question}

Give a brief hint (1-2 sentences) that guides the student without giving away the answer."""

    def _build_explanation_prompt(
        self,
        question: str,
        correct_answer: str,
        user_answer: str = None,
    ) -> str:
        """Build the prompt for explanation generation."""
        if user_answer and user_answer.lower() != correct_answer.lower():
            return f"""Explain why the correct answer to this question is '{correct_answer}',
and briefly explain what was wrong with the answer '{user_answer}':

Question: {question}

Provide a clear, educational explanation that helps the student understand their mistake."""

        return f"""Explain why the answer to this question is '{correct_answer}' and
how to solve it step-by-step:

Question: {question}

Provide a clear explanation of the concept and solution."""

    def _parse_question_response(self, response_text: str) -> Optional[Dict]:
        """Parse JSON response from Gemini."""
        try:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1

            if start == -1 or end == 0:
                return None

            json_str = response_text[start:end]
            data = json.loads(json_str)

            if not all(
                key in data
                for key in ["question", "answer", "explanation", "hints"]
            ):
                return None

            return {
                "question": data["question"],
                "answer": str(data["answer"]).strip(),
                "explanation": data["explanation"],
                "hints": data.get("hints", []),
            }
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing Gemini response: {e}")
            return None

    def _get_dummy_question(
        self, topic: str, difficulty: DifficultyLevel
    ) -> Dict:
        """
        Return a demo question when API access is unavailable.

        The fallback should still let the rest of the backend run normally.
        """
        dummy_questions = {
            ("arithmetic", "easy"): {
                "question": "What is 2 + 3?",
                "answer": "5",
                "explanation": "2 + 3 = 5. You add the numbers together.",
                "hints": ["Count on your fingers", "5 comes after 4"],
            },
            ("algebra", "medium"): {
                "question": "Solve for x: 2x + 6 = 14",
                "answer": "4",
                "explanation": "Subtract 6 from both sides to get 2x = 8, then divide by 2 to get x = 4.",
                "hints": [
                    "Undo the +6 first",
                    "After subtracting 6, divide both sides by 2",
                ],
            },
            ("geometry", "easy"): {
                "question": "What is the area of a rectangle with length 6 and width 4?",
                "answer": "24",
                "explanation": "Area of a rectangle is length times width, so 6 x 4 = 24.",
                "hints": [
                    "Use the rectangle area formula",
                    "Multiply the side lengths",
                ],
            },
            ("trigonometry", "medium"): {
                "question": "What is cos(pi/3)?",
                "answer": "1/2",
                "explanation": "pi/3 radians is 60 degrees, and cos(60 degrees) = 1/2.",
                "hints": [
                    "Convert pi/3 radians to degrees",
                    "Use the unit circle value for 60 degrees",
                ],
            },
            ("calculus", "hard"): {
                "question": "What is the derivative of f(x) = x^3e^x?",
                "answer": "x^2e^x(x + 3)",
                "explanation": "Use the product rule: d/dx(uv) = u'v + uv'. This becomes 3x^2e^x + x^3e^x = x^2e^x(x + 3).",
                "hints": [
                    "Remember the product rule",
                    "Derivative of e^x is e^x",
                ],
            },
            ("statistics", "easy"): {
                "question": "What is the mean of 2, 4, and 6?",
                "answer": "4",
                "explanation": "Add the numbers to get 12, then divide by 3 to get 4.",
                "hints": [
                    "Find the total first",
                    "Divide by how many numbers there are",
                ],
            },
            ("logarithms", "medium"): {
                "question": "What is log10(1000)?",
                "answer": "3",
                "explanation": "10^3 = 1000, so log base 10 of 1000 is 3.",
                "hints": [
                    "Think of the exponent on 10",
                    "10 times itself 3 times equals 1000",
                ],
            },
        }

        default = {
            "question": f"[DEMO] Solve for x: x + 7 = 12 ({topic}, {difficulty.value})",
            "answer": "5",
            "explanation": "Subtract 7 from both sides to isolate x, which gives x = 5.",
            "hints": [
                "Move the constant from the left side",
                "Subtract 7 from 12",
            ],
        }

        return dummy_questions.get((topic.lower(), difficulty.value), default)

    def _get_dummy_hint(self, question: str, hint_number: int) -> str:
        """Return a dummy hint when API is unavailable."""
        if hint_number == 1:
            return "Think about the key concept underlying this problem."
        return "Try breaking the problem into smaller steps."


gemini_client = GeminiIntegration()
