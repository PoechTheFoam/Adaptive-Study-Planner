"""
Gemini API Integration for the Adaptive Learning Platform

Handles:
- Question generation
- Hint generation
- Explanation generation
"""
import json
from typing import List, Optional, Dict
import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_CONFIG
from models import DifficultyLevel


# Configure Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class GeminiIntegration:
    """Integration with Google's Gemini API for content generation"""
    
    def __init__(self):
        self.model_name = GEMINI_CONFIG["model"]
        self.temperature = GEMINI_CONFIG["temperature"]
        self.max_tokens = GEMINI_CONFIG["max_output_tokens"]
        self.api_key = GEMINI_API_KEY
        
        if not self.api_key:
            print("⚠️  WARNING: Gemini API key not configured!")
    
    def generate_question(
        self,
        topic: str,
        difficulty: DifficultyLevel,
        skill_level: str,
        goal: str
    ) -> Optional[Dict]:
        """
        Generate a question using Gemini API.
        
        ⚠️  IMPORTANT: Make sure your GEMINI_API_KEY is set in config.py!
        
        Args:
            topic: Mathematical topic (e.g., "trigonometry identities")
            difficulty: Difficulty level (easy, medium, hard)
            skill_level: User's skill level (beginner, intermediate, advanced)
            goal: Learning goal (exam, mastery, speed)
            
        Returns:
            Dictionary with keys: question, answer, explanation, hints
            Returns None if API fails
        """
        
        if not self.api_key:
            print("❌ ERROR: Cannot generate question - Gemini API key not set!")
            return self._get_dummy_question(topic, difficulty)
        
        try:
            prompt = self._build_question_prompt(topic, difficulty, skill_level, goal)
            
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            )
            
            # Parse response
            return self._parse_question_response(response.text)
            
        except Exception as e:
            print(f"❌ Error generating question: {e}")
            return self._get_dummy_question(topic, difficulty)
    
    def generate_hint(
        self,
        question: str,
        topic: str,
        hint_number: int = 1
    ) -> Optional[str]:
        """
        Generate a hint for a question using Gemini API.
        
        Args:
            question: The question text
            topic: The topic of the question
            hint_number: Which hint number (1, 2, etc.)
            
        Returns:
            String with the hint, or None if API fails
        """
        
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
                )
            )
            
            return response.text.strip()
            
        except Exception as e:
            print(f"❌ Error generating hint: {e}")
            return self._get_dummy_hint(question, hint_number)
    
    def generate_explanation(
        self,
        question: str,
        correct_answer: str,
        user_answer: str = None
    ) -> Optional[str]:
        """
        Generate an explanation for why an answer is correct.
        
        Args:
            question: The question text
            correct_answer: The correct answer
            user_answer: User's answer (optional, for explaining why it's wrong)
            
        Returns:
            String with the explanation
        """
        
        if not self.api_key:
            return f"The correct answer is '{correct_answer}'. Please review the concept."
        
        try:
            prompt = self._build_explanation_prompt(question, correct_answer, user_answer)
            
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=800,
                )
            )
            
            return response.text.strip()
            
        except Exception as e:
            print(f"❌ Error generating explanation: {e}")
            return f"The correct answer is '{correct_answer}'."
    
    def _build_question_prompt(
        self,
        topic: str,
        difficulty: DifficultyLevel,
        skill_level: str,
        goal: str
    ) -> str:
        """Build the prompt for question generation"""
        
        difficulty_description = {
            "easy": "basic concept, simple calculation",
            "medium": "requires multiple steps, moderate difficulty",
            "hard": "advanced, requires problem-solving skills"
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
        hint_number: int
    ) -> str:
        """Build the prompt for hint generation"""
        
        if hint_number == 1:
            hint_type = "a general approach or concept to consider"
        else:
            hint_type = "a more specific clue or next step"
        
        prompt = f"""For this {topic} question, provide {hint_type}:

Question: {question}

Give a brief hint (1-2 sentences) that guides the student without giving away the answer."""
        
        return prompt
    
    def _build_explanation_prompt(
        self,
        question: str,
        correct_answer: str,
        user_answer: str = None
    ) -> str:
        """Build the prompt for explanation generation"""
        
        if user_answer and user_answer.lower() != correct_answer.lower():
            prompt = f"""Explain why the correct answer to this question is '{correct_answer}', 
and briefly explain what was wrong with the answer '{user_answer}':

Question: {question}

Provide a clear, educational explanation that helps the student understand their mistake."""
        else:
            prompt = f"""Explain why the answer to this question is '{correct_answer}' and 
how to solve it step-by-step:

Question: {question}

Provide a clear explanation of the concept and solution."""
        
        return prompt
    
    def _parse_question_response(self, response_text: str) -> Optional[Dict]:
        """Parse JSON response from Gemini"""
        try:
            # Find JSON in response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start == -1 or end == 0:
                return None
            
            json_str = response_text[start:end]
            data = json.loads(json_str)
            
            # Validate required fields
            if not all(key in data for key in ["question", "answer", "explanation", "hints"]):
                return None
            
            return {
                "question": data["question"],
                "answer": str(data["answer"]).strip(),
                "explanation": data["explanation"],
                "hints": data.get("hints", [])
            }
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing Gemini response: {e}")
            return None
    
    def _get_dummy_question(self, topic: str, difficulty: DifficultyLevel) -> Dict:
        """
        Return a dummy question when API is unavailable.
        Used for testing and development.
        """
        dummy_questions = {
            ("basic algebra", "easy"): {
                "question": "What is 2 + 3?",
                "answer": "5",
                "explanation": "2 + 3 = 5. You add the numbers together.",
                "hints": ["Count on your fingers", "5 comes after 4"]
            },
            ("trigonometry identities", "medium"): {
                "question": "If sin(θ) = 0.5, what is cos(π/6)?",
                "answer": "√3/2",
                "explanation": "cos(π/6) = √3/2 ≈ 0.866. This is a fundamental trig identity.",
                "hints": ["π/6 radians = 30°", "Use the unit circle"]
            },
            ("calculus", "hard"): {
                "question": "What is the derivative of f(x) = x³e^x?",
                "answer": "x²e^x(x + 3) or x²e^x(3 + x)",
                "explanation": "Use the product rule: d/dx(uv) = u'v + uv'",
                "hints": ["Remember the product rule", "Derivative of e^x is e^x"]
            }
        }
        
        default = {
            "question": f"[DEMO] Solve this {difficulty.value} {topic} problem...",
            "answer": "[SET YOUR GEMINI_API_KEY]",
            "explanation": "API key needed to generate real questions.",
            "hints": ["🔑 Add GEMINI_API_KEY=your_key to config.py", "Or set it as an environment variable"]
        }
        
        return dummy_questions.get((topic.lower(), difficulty.value), default)
    
    def _get_dummy_hint(self, question: str, hint_number: int) -> str:
        """Return a dummy hint when API is unavailable"""
        if hint_number == 1:
            return "Think about the key concept underlying this problem."
        else:
            return "Try breaking the problem into smaller steps."


# Global Gemini integration instance
gemini_client = GeminiIntegration()
