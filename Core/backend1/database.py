"""
Database management for the Adaptive Learning Platform.

Handles:
- SQLite database setup
- CRUD operations
- Data persistence
"""
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import List, Optional

from config import DATABASE_CONFIG
from models import (
    DifficultyLevel,
    Exercise,
    Goal,
    MasteryStatus,
    SkillLevel,
    TopicPerformance,
    UserAnswer,
    UserProfile,
)


class Database:
    """SQLite database manager."""

    def __init__(self):
        self.db_path = DATABASE_CONFIG["db_path"]
        self.conn: Optional[sqlite3.Connection] = None
        self.lock = Lock()
        self._initialize_db()

    def _initialize_db(self):
        """Initialize database connection and create tables."""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._create_tables()
            print(f"Database initialized at {self.db_path}")
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def _create_tables(self):
        """Create all necessary tables."""
        with self.lock:
            cursor = self.conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    skill_level TEXT NOT NULL,
                    goal TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    total_questions_answered INTEGER DEFAULT 0,
                    current_topic TEXT DEFAULT '',
                    current_difficulty TEXT DEFAULT 'medium',
                    overall_mastery REAL DEFAULT 0.0,
                    average_response_time REAL DEFAULT 0.0
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS exercises (
                    exercise_id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    hints TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    exercise_id TEXT NOT NULL,
                    user_answer TEXT NOT NULL,
                    is_correct INTEGER NOT NULL,
                    response_time REAL NOT NULL,
                    hints_used INTEGER DEFAULT 0,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (exercise_id) REFERENCES exercises(exercise_id)
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS topic_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    questions_answered INTEGER DEFAULT 0,
                    questions_correct INTEGER DEFAULT 0,
                    mastery_score REAL DEFAULT 0.0,
                    mastery_status TEXT DEFAULT 'learning',
                    average_response_time REAL DEFAULT 0.0,
                    recent_scores TEXT DEFAULT '[]',
                    confidence_level TEXT DEFAULT 'medium',
                    last_updated TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    UNIQUE(user_id, topic)
                )
                """
            )

            self.conn.commit()

    # ========== USER OPERATIONS ==========

    def create_user(self, user_profile: UserProfile) -> bool:
        """Create a new user."""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_profile.user_id,
                        user_profile.name,
                        user_profile.skill_level.value,
                        user_profile.goal.value,
                        user_profile.created_at.isoformat(),
                        user_profile.total_questions_answered,
                        user_profile.current_topic,
                        user_profile.current_difficulty.value,
                        user_profile.overall_mastery,
                        user_profile.average_response_time,
                    ),
                )
                self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"User {user_profile.user_id} already exists")
            return False

    def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Get user by ID."""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
                )
                row = cursor.fetchone()

            if not row:
                return None

            return UserProfile(
                user_id=row[0],
                name=row[1],
                skill_level=SkillLevel(row[2]),
                goal=Goal(row[3]),
                created_at=datetime.fromisoformat(row[4]),
                total_questions_answered=row[5],
                current_topic=row[6],
                current_difficulty=DifficultyLevel(row[7]),
                overall_mastery=row[8],
                average_response_time=row[9],
            )
        except Exception as e:
            print(f"Error fetching user: {e}")
            return None

    def update_user(self, user_profile: UserProfile) -> bool:
        """Update user profile."""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    """
                    UPDATE users SET
                        name = ?, skill_level = ?, goal = ?,
                        total_questions_answered = ?,
                        current_topic = ?, current_difficulty = ?,
                        overall_mastery = ?, average_response_time = ?
                    WHERE user_id = ?
                    """,
                    (
                        user_profile.name,
                        user_profile.skill_level.value,
                        user_profile.goal.value,
                        user_profile.total_questions_answered,
                        user_profile.current_topic,
                        user_profile.current_difficulty.value,
                        user_profile.overall_mastery,
                        user_profile.average_response_time,
                        user_profile.user_id,
                    ),
                )
                self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating user: {e}")
            return False

    # ========== EXERCISE OPERATIONS ==========

    def create_exercise(self, exercise: Exercise) -> bool:
        """Save an exercise to database."""
        try:
            hints_json = json.dumps(exercise.hints)
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO exercises VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        exercise.exercise_id,
                        exercise.topic,
                        exercise.difficulty.value,
                        exercise.question,
                        exercise.answer,
                        exercise.explanation,
                        hints_json,
                        datetime.now().isoformat(),
                    ),
                )
                self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            print(f"Exercise {exercise.exercise_id} already exists")
            return False

    def get_exercise(self, exercise_id: str) -> Optional[Exercise]:
        """Get exercise by ID."""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT * FROM exercises WHERE exercise_id = ?",
                    (exercise_id,),
                )
                row = cursor.fetchone()

            if not row:
                return None

            return Exercise(
                exercise_id=row[0],
                topic=row[1],
                difficulty=DifficultyLevel(row[2]),
                question=row[3],
                answer=row[4],
                explanation=row[5],
                hints=json.loads(row[6]),
            )
        except Exception as e:
            print(f"Error fetching exercise: {e}")
            return None

    def get_exercises_by_topic_difficulty(
        self,
        topic: str,
        difficulty: DifficultyLevel,
    ) -> List[Exercise]:
        """Get exercises by topic and difficulty."""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT * FROM exercises WHERE topic = ? AND difficulty = ?",
                    (topic, difficulty.value),
                )
                rows = cursor.fetchall()

            exercises = []
            for row in rows:
                exercises.append(
                    Exercise(
                        exercise_id=row[0],
                        topic=row[1],
                        difficulty=DifficultyLevel(row[2]),
                        question=row[3],
                        answer=row[4],
                        explanation=row[5],
                        hints=json.loads(row[6]),
                    )
                )
            return exercises
        except Exception as e:
            print(f"Error fetching exercises: {e}")
            return []

    # ========== USER ANSWER OPERATIONS ==========

    def save_answer(self, user_answer: UserAnswer) -> bool:
        """Save user's answer to database."""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO user_answers
                    (user_id, exercise_id, user_answer, is_correct, response_time, hints_used, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user_answer.user_id,
                        user_answer.exercise_id,
                        user_answer.user_answer,
                        1 if user_answer.is_correct else 0,
                        user_answer.response_time,
                        user_answer.hints_used,
                        user_answer.timestamp.isoformat(),
                    ),
                )
                self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving answer: {e}")
            return False

    def get_user_answers(
        self, user_id: str, limit: int = None
    ) -> List[UserAnswer]:
        """Get all answers from a user."""
        try:
            query = "SELECT * FROM user_answers WHERE user_id = ? ORDER BY timestamp DESC"
            if limit:
                query += f" LIMIT {limit}"

            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(query, (user_id,))
                rows = cursor.fetchall()

            answers = []
            for row in rows:
                answers.append(
                    UserAnswer(
                        user_id=row[1],
                        exercise_id=row[2],
                        user_answer=row[3],
                        is_correct=bool(row[4]),
                        response_time=row[5],
                        hints_used=row[6],
                        timestamp=datetime.fromisoformat(row[7]),
                    )
                )
            return answers
        except Exception as e:
            print(f"Error fetching answers: {e}")
            return []

    def get_user_answers_for_topic(
        self, user_id: str, topic: str
    ) -> List[UserAnswer]:
        """Get answers for a specific topic."""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    """
                    SELECT ua.* FROM user_answers ua
                    JOIN exercises e ON ua.exercise_id = e.exercise_id
                    WHERE ua.user_id = ? AND e.topic = ?
                    ORDER BY ua.timestamp
                    """,
                    (user_id, topic),
                )
                rows = cursor.fetchall()

            answers = []
            for row in rows:
                answers.append(
                    UserAnswer(
                        user_id=row[1],
                        exercise_id=row[2],
                        user_answer=row[3],
                        is_correct=bool(row[4]),
                        response_time=row[5],
                        hints_used=row[6],
                        timestamp=datetime.fromisoformat(row[7]),
                    )
                )
            return answers
        except Exception as e:
            print(f"Error fetching topic answers: {e}")
            return []

    # ========== TOPIC PERFORMANCE OPERATIONS ==========

    def save_topic_performance(
        self, user_id: str, performance: TopicPerformance
    ) -> bool:
        """Save or update topic performance."""
        try:
            recent_scores_json = json.dumps(performance.recent_scores)
            now = datetime.now().isoformat()

            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT id FROM topic_performance WHERE user_id = ? AND topic = ?",
                    (user_id, performance.topic),
                )

                if cursor.fetchone():
                    cursor.execute(
                        """
                        UPDATE topic_performance SET
                            questions_answered = ?, questions_correct = ?,
                            mastery_score = ?, mastery_status = ?,
                            average_response_time = ?, recent_scores = ?,
                            confidence_level = ?, last_updated = ?
                        WHERE user_id = ? AND topic = ?
                        """,
                        (
                            performance.questions_answered,
                            performance.questions_correct,
                            performance.mastery_score,
                            performance.mastery_status.value,
                            performance.average_response_time,
                            recent_scores_json,
                            performance.confidence_level,
                            now,
                            user_id,
                            performance.topic,
                        ),
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO topic_performance
                        (user_id, topic, questions_answered, questions_correct,
                         mastery_score, mastery_status, average_response_time,
                         recent_scores, confidence_level, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            user_id,
                            performance.topic,
                            performance.questions_answered,
                            performance.questions_correct,
                            performance.mastery_score,
                            performance.mastery_status.value,
                            performance.average_response_time,
                            recent_scores_json,
                            performance.confidence_level,
                            now,
                        ),
                    )

                self.conn.commit()
            return True
        except Exception as e:
            print(f"Error saving topic performance: {e}")
            return False

    def get_topic_performance(
        self, user_id: str, topic: str
    ) -> Optional[TopicPerformance]:
        """Get performance for a specific topic."""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT * FROM topic_performance WHERE user_id = ? AND topic = ?",
                    (user_id, topic),
                )
                row = cursor.fetchone()

            if not row:
                return None

            return TopicPerformance(
                topic=row[2],
                questions_answered=row[3],
                questions_correct=row[4],
                mastery_score=row[5],
                mastery_status=MasteryStatus(row[6]),
                average_response_time=row[7],
                recent_scores=json.loads(row[8]),
                confidence_level=row[9],
            )
        except Exception as e:
            print(f"Error fetching topic performance: {e}")
            return None

    def get_all_topic_performance(
        self, user_id: str
    ) -> List[TopicPerformance]:
        """Get performance across all topics."""
        try:
            with self.lock:
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT * FROM topic_performance WHERE user_id = ? ORDER BY topic",
                    (user_id,),
                )
                rows = cursor.fetchall()

            performances = []
            for row in rows:
                performances.append(
                    TopicPerformance(
                        topic=row[2],
                        questions_answered=row[3],
                        questions_correct=row[4],
                        mastery_score=row[5],
                        mastery_status=MasteryStatus(row[6]),
                        average_response_time=row[7],
                        recent_scores=json.loads(row[8]),
                        confidence_level=row[9],
                    )
                )
            return performances
        except Exception as e:
            print(f"Error fetching all topic performance: {e}")
            return []

    def close(self):
        """Close database connection."""
        if self.conn:
            with self.lock:
                self.conn.close()


# Global database instance
db = Database()
