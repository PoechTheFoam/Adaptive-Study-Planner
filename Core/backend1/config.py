"""
Configuration file for the Adaptive Learning Platform Backend.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ============================================================================
# IMPORTANT: API KEY CONFIGURATION
# ============================================================================
# REMINDER: Add your Gemini API key here!
# You can either:
# 1. Set the environment variable: GEMINI_API_KEY=your_key_here
# 2. Create a .env file in the backend directory with: GEMINI_API_KEY=your_key_here
# 3. Set it directly below (not recommended for production)
# ============================================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DATABASE_PATH = os.getenv(
    "DATABASE_PATH", str(BASE_DIR / "adaptive_learning.db")
)
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
UVICORN_RELOAD = os.getenv("UVICORN_RELOAD", "true").lower() == "true"

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY not set! Please set your API key.")
    print("Add GEMINI_API_KEY to your .env file or environment variables.")

# Platform Configuration
PLATFORM_CONFIG = {
    "name": "Adaptive Learning Platform",
    "version": "1.0.0",
}

# Scoring Configuration
SCORING_CONFIG = {
    "difficulty_multipliers": {
        "easy": 0.8,
        "medium": 1.0,
        "hard": 1.2,
    },
    "hint_penalties": {
        0: 1.0,  # No hints
        1: 0.6,  # 1 hint used
        2: 0.2,  # 2+ hints used
    },
    "mastery_window": 3,  # Calculate mastery over last 3 questions
}

# Decision Engine Thresholds
DECISION_ENGINE_CONFIG = {
    "mastery_high_threshold": 0.85,  # > 85%: increase difficulty
    "mastery_low_threshold": 0.50,  # < 50%: review mode
    "time_multiplier_threshold": 2.0,  # 2x average time = struggling
    "min_questions_for_mastery": 3,  # Need at least 3 questions before deciding
}

# Gemini API Configuration
GEMINI_CONFIG = {
    "model": "gemini-1.5-flash",
    "temperature": 0.7,
    "max_output_tokens": 1000,
}

# Database Configuration
DATABASE_CONFIG = {
    "db_type": "sqlite",
    "db_path": DATABASE_PATH,
}

# Exercise Difficulty Levels
DIFFICULTY_LEVELS = ["easy", "medium", "hard"]

# Topics (can be expanded)
TOPICS = [
    "arithmetic",
    "algebra",
    "geometry",
    "trigonometry",
    "calculus",
    "statistics",
    "logarithms",
]

# Skill Levels
SKILL_LEVELS = ["beginner", "intermediate", "advanced"]

# Goals
GOALS = ["exam", "mastery", "speed"]
