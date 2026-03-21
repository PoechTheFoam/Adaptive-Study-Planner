"""
Unit tests for the Adaptive Learning Platform Backend

Run with: pytest -v test_backend.py
"""
import pytest
from models import (
    UserProfile,
    Exercise,
    UserAnswer,
    DifficultyLevel,
    SkillLevel,
    Goal,
    QuestionScore,
    TopicPerformance,
    MasteryStatus,
)
from scoring import scoring_engine
from decision_engine import decision_engine


class TestScoringEngine:
    """Test the scoring engine"""

    def test_calculate_question_score_correct_no_hints(self):
        """Test scoring for correct answer without hints"""
        score = scoring_engine.calculate_question_score(
            is_correct=True, difficulty=DifficultyLevel.MEDIUM, hints_used=0
        )

        assert score.base == 1.0
        assert score.difficulty_multiplier == 1.0
        assert score.hint_penalty == 1.0
        assert score.score == 1.0

    def test_calculate_question_score_correct_with_hint(self):
        """Test scoring for correct answer with 1 hint"""
        score = scoring_engine.calculate_question_score(
            is_correct=True, difficulty=DifficultyLevel.HARD, hints_used=1
        )

        assert score.base == 1.0
        assert score.difficulty_multiplier == 1.2
        assert score.hint_penalty == 0.6
        assert score.score == pytest.approx(0.72, 0.01)

    def test_calculate_question_score_incorrect(self):
        """Test scoring for incorrect answer"""
        score = scoring_engine.calculate_question_score(
            is_correct=False, difficulty=DifficultyLevel.EASY, hints_used=0
        )

        assert score.base == 0.0
        assert score.score == 0.0

    def test_calculate_average_score(self):
        """Test average score calculation"""
        scores = [
            QuestionScore(
                base=1.0, difficulty_multiplier=1.0, hint_penalty=1.0
            ),
            QuestionScore(
                base=1.0, difficulty_multiplier=1.0, hint_penalty=0.6
            ),
            QuestionScore(
                base=0.0, difficulty_multiplier=1.0, hint_penalty=1.0
            ),
        ]

        avg = scoring_engine.calculate_average_score(scores)
        expected = (1.0 + 0.6 + 0.0) / 3
        assert avg == pytest.approx(expected, 0.01)

    def test_calculate_mastery(self):
        """Test mastery score calculation"""
        mastery = scoring_engine.calculate_mastery(
            accuracy=80.0, consistency=0.8
        )

        assert mastery == pytest.approx(64.0, 0.1)  # 0.8 * 0.8 * 100

    def test_determine_mastery_status_proficient(self):
        """Test mastery status determination - proficient"""
        status = scoring_engine.determine_mastery_status(90.0)
        assert status == MasteryStatus.PROFICIENT

    def test_determine_mastery_status_struggling(self):
        """Test mastery status determination - struggling"""
        status = scoring_engine.determine_mastery_status(30.0)
        assert status == MasteryStatus.STRUGGLING

    def test_determine_mastery_status_learning(self):
        """Test mastery status determination - learning"""
        status = scoring_engine.determine_mastery_status(65.0)
        assert status == MasteryStatus.LEARNING

    def test_calculate_consistency_all_correct(self):
        """Test consistency calculation - all correct"""
        consistency = scoring_engine.calculate_consistency([True, True, True])
        assert consistency == 1.0

    def test_calculate_consistency_mixed(self):
        """Test consistency calculation - mixed results"""
        consistency = scoring_engine.calculate_consistency(
            [True, False, True, False]
        )
        # Variance = (2 * 2) / 16 = 0.25, so consistency = 0.75
        assert consistency == pytest.approx(0.75, 0.01)


class TestDecisionEngine:
    """Test the decision engine"""

    def test_increase_difficulty(self):
        """Test difficulty increase"""
        new_diff = decision_engine._increase_difficulty(DifficultyLevel.EASY)
        assert new_diff == DifficultyLevel.MEDIUM

        new_diff = decision_engine._increase_difficulty(DifficultyLevel.HARD)
        assert new_diff == DifficultyLevel.HARD  # Already at max

    def test_decrease_difficulty(self):
        """Test difficulty decrease"""
        new_diff = decision_engine._decrease_difficulty(DifficultyLevel.HARD)
        assert new_diff == DifficultyLevel.MEDIUM

        new_diff = decision_engine._decrease_difficulty(DifficultyLevel.EASY)
        assert new_diff == DifficultyLevel.EASY  # Already at min

    def test_should_give_hint_struggling(self):
        """Test hint offering for struggling students"""
        should_hint = decision_engine.should_give_hint(
            hints_already_used=0,
            mastery_score=30.0,  # Struggling
            question_difficulty=DifficultyLevel.EASY,
        )
        assert should_hint is True

    def test_should_give_hint_no_more_than_2(self):
        """Test that max 2 hints are offered"""
        should_hint = decision_engine.should_give_hint(
            hints_already_used=2,
            mastery_score=50.0,
            question_difficulty=DifficultyLevel.MEDIUM,
        )
        assert should_hint is False

    def test_should_explain_wrong_answer(self):
        """Test that wrong answers always get explanation"""
        should_explain = decision_engine.should_explain(
            is_correct=False, mastery_score=90.0
        )
        assert should_explain is True

    def test_should_explain_struggling_student(self):
        """Test that struggling students get explanation"""
        should_explain = decision_engine.should_explain(
            is_correct=True, mastery_score=40.0
        )
        assert should_explain is True

    def test_get_next_topic(self):
        """Test topic progression"""
        all_topics = ["algebra", "geometry", "calculus"]

        next_topic = decision_engine._get_next_topic("algebra", all_topics)
        assert next_topic == "geometry"

        next_topic = decision_engine._get_next_topic("calculus", all_topics)
        assert next_topic == "calculus"  # Already last


class TestModels:
    """Test data models"""

    def test_user_profile_creation(self):
        """Test creating user profile"""
        user = UserProfile(
            user_id="test-user",
            name="John Doe",
            skill_level=SkillLevel.BEGINNER,
            goal=Goal.MASTERY,
        )

        assert user.user_id == "test-user"
        assert user.name == "John Doe"
        assert user.overall_mastery == 0.0

    def test_exercise_creation(self):
        """Test creating exercise"""
        exercise = Exercise(
            exercise_id="ex-1",
            topic="algebra",
            difficulty=DifficultyLevel.MEDIUM,
            question="What is 2+2?",
            answer="4",
            explanation="2+2=4",
            hints=["Think of numbers", "Count"],
        )

        assert exercise.question == "What is 2+2?"
        assert len(exercise.hints) == 2

    def test_topic_performance_accuracy(self):
        """Test topic performance accuracy calculation"""
        perf = TopicPerformance(
            topic="algebra", questions_answered=10, questions_correct=8
        )

        assert perf.accuracy == 80.0

    def test_question_score_calculation(self):
        """Test question score calculation"""
        score = QuestionScore(
            base=1.0, difficulty_multiplier=1.2, hint_penalty=0.6
        )

        assert score.score == pytest.approx(0.72, 0.01)


class TestIntegration:
    """Integration tests"""

    def test_scoring_workflow(self):
        """Test complete scoring workflow"""
        # Create a user answer
        answer = UserAnswer(
            user_id="user-1",
            exercise_id="ex-1",
            user_answer="4",
            is_correct=True,
            response_time=10.0,
            hints_used=0,
        )

        # Create exercise
        exercise = Exercise(
            exercise_id="ex-1",
            topic="algebra",
            difficulty=DifficultyLevel.MEDIUM,
            question="What is 2+2?",
            answer="4",
            explanation="2+2=4",
        )

        # Calculate score
        score = scoring_engine.calculate_question_score(
            is_correct=answer.is_correct,
            difficulty=exercise.difficulty,
            hints_used=answer.hints_used,
        )

        assert score.score == 1.0

    def test_mastery_calculation_workflow(self):
        """Test complete mastery calculation workflow"""
        # Simulate answers
        results = [True, True, False]  # 2 correct, 1 incorrect

        # Calculate accuracy
        accuracy = (sum(results) / len(results)) * 100

        # Calculate consistency
        consistency = scoring_engine.calculate_consistency(results)

        # Calculate mastery
        mastery = scoring_engine.calculate_mastery(accuracy, consistency)

        # Determine status
        status = scoring_engine.determine_mastery_status(mastery)

        assert accuracy == pytest.approx(66.67, 0.1)
        assert status in [MasteryStatus.LEARNING, MasteryStatus.STRUGGLING]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
