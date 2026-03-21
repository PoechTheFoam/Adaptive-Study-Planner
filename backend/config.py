"""
Configuration file for the Adaptive Learning Platform Backend
"""
import os

GEMINI_API_KEY = "AIzaSyDzG6cd1oiMMajUo00f_sgrCuTtnIt2QzU"
# ============================================================================
# IMPORTANT: API KEY CONFIGURATION
# ============================================================================
# REMINDER: Add your Gemini API key here!
# You can either:
# 1. Set the environment variable: GEMINI_API_KEY=your_key_here
# 2. Create a .env file in the root directory with: GEMINI_API_KEY=your_key_here
# 3. Set it directly below (NOT recommended for production)
# ============================================================================

if not GEMINI_API_KEY:
    print("⚠️  WARNING: GEMINI_API_KEY not set! Please set your API key.")
    print("   Add GEMINI_API_KEY to your .env file or environment variables.")

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
        0: 1.0,      # No hints
        1: 0.6,      # 1 hint used
        2: 0.2,      # 2+ hints used
    },
    "mastery_window": 3,  # Calculate mastery over last 3 questions
}

# Decision Engine Thresholds
DECISION_ENGINE_CONFIG = {
    "mastery_high_threshold": 0.85,    # > 85%: increase difficulty
    "mastery_low_threshold": 0.50,     # < 50%: review mode
    "time_multiplier_threshold": 2.0,  # 2x average time = struggling
    "min_questions_for_mastery": 3,    # Need at least 3 questions before deciding
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
    "db_path": "adaptive_learning.db",
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
