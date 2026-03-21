"""
Data models for the Adaptive Learning Platform
"""
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DifficultyLevel(str, Enum):
    """Difficulty levels for exercises"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SkillLevel(str, Enum):
    """User skill levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Goal(str, Enum):
    """User learning goals"""
    EXAM = "exam"
    MASTERY = "mastery"
    SPEED = "speed"


class MasteryStatus(str, Enum):
    """Mastery status of a topic"""
    STRUGGLING = "struggling"      # Mastery < 50%
    LEARNING = "learning"          # 50% <= Mastery <= 85%
    PROFICIENT = "proficient"      # Mastery > 85%
    UNSTABLE = "unstable"          # Inconsistent performance


@dataclass
class UserProfile:
    """User profile and learning state"""
    user_id: str
    name: str
    skill_level: SkillLevel
    goal: Goal
    created_at: datetime = field(default_factory=datetime.now)
    
    # Tracking
    total_questions_answered: int = 0
    current_topic: str = ""
    current_difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    
    # Performance metrics
    overall_mastery: float = 0.0  # 0-100%
    average_response_time: float = 0.0  # seconds
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "skill_level": self.skill_level.value,
            "goal": self.goal.value,
            "created_at": self.created_at.isoformat(),
            "total_questions_answered": self.total_questions_answered,
            "current_topic": self.current_topic,
            "current_difficulty": self.current_difficulty.value,
            "overall_mastery": self.overall_mastery,
            "average_response_time": self.average_response_time,
        }


@dataclass
class Exercise:
    """Exercise/Question structure"""
    exercise_id: str
    topic: str
    difficulty: DifficultyLevel
    question: str
    answer: str  # Correct answer
    explanation: str  # Why the answer is correct
    hints: List[str] = field(default_factory=list)  # Progressive hints
    
    def to_dict(self):
        return {
            "exercise_id": self.exercise_id,
            "topic": self.topic,
            "difficulty": self.difficulty.value,
            "question": self.question,
            "explanation": self.explanation,
            "hints": self.hints,
            # Don't include the answer in response to client
        }


@dataclass
class UserAnswer:
    """Record of user's answer to a question"""
    user_id: str
    exercise_id: str
    user_answer: str
    is_correct: bool
    response_time: float  # seconds
    conceptual_match: bool
    understanding: str
    hints_used: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "exercise_id": self.exercise_id,
            "is_correct": self.is_correct,
            "response_time": self.response_time,
            "hints_used": self.hints_used,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class QuestionScore:
    """Score for a single question using weighted scoring formula"""
    base: float  # 1.0 for correct, 0.0 for incorrect
    difficulty_multiplier: float  # 0.8 (easy), 1.0 (medium), 1.2 (hard)
    hint_penalty: float  # 1.0 (no hints), 0.6 (1 hint), 0.2 (2+ hints)
    
    @property
    def score(self) -> float:
        """Calculate score: Base × Difficulty × HintPenalty"""
        return self.base * self.difficulty_multiplier * self.hint_penalty
    
    def to_dict(self):
        return {
            "base": self.base,
            "difficulty_multiplier": self.difficulty_multiplier,
            "hint_penalty": self.hint_penalty,
            "score": self.score,
        }


@dataclass
class TopicPerformance:
    """Performance tracking for a specific topic"""
    topic: str
    questions_answered: int = 0
    questions_correct: int = 0
    mastery_score: float = 0.0  # 0-100%
    mastery_status: MasteryStatus = MasteryStatus.LEARNING
    average_response_time: float = 0.0
    recent_scores: List[float] = field(default_factory=list)  # Last N scores
    confidence_level: str = "medium"  # low, medium, high
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy percentage"""
        if self.questions_answered == 0:
            return 0.0
        return (self.questions_correct / self.questions_answered) * 100
    
    def to_dict(self):
        return {
            "topic": self.topic,
            "questions_answered": self.questions_answered,
            "questions_correct": self.questions_correct,
            "accuracy": f"{self.accuracy:.1f}%",
            "mastery_score": f"{self.mastery_score:.1f}%",
            "mastery_status": self.mastery_status.value,
            "average_response_time": f"{self.average_response_time:.2f}s",
            "confidence_level": self.confidence_level,
        }


@dataclass
class NextActionDecision:
    """Decision from the AI brain for what to do next"""
    action: str  # "next_question", "explain", "review", "advance"
    recommended_difficulty: DifficultyLevel
    recommended_topic: str
    reason: str
    should_give_hint: bool = False
    should_review: bool = False
    should_advance: bool = False
    feedback: str = ""
    
    def to_dict(self):
        return {
            "action": self.action,
            "recommended_difficulty": self.recommended_difficulty.value,
            "recommended_topic": self.recommended_topic,
            "reason": self.reason,
            "should_give_hint": self.should_give_hint,
            "should_review": self.should_review,
            "should_advance": self.should_advance,
            "feedback": self.feedback,
        }
