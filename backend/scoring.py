"""
Scoring engine for the Adaptive Learning Platform

Implements the weighted scoring formula:
Score = (1/n) × Σ(Base × Difficulty × HintPenalty)
"""
from typing import List
from models import QuestionScore, DifficultyLevel, MasteryStatus, UserAnswer, TopicPerformance
from config import SCORING_CONFIG, DECISION_ENGINE_CONFIG
from collections import defaultdict


class ScoringEngine:
    """Calculate scores and mastery levels for users"""
    
    def __init__(self):
        self.config = SCORING_CONFIG
        self.decision_config = DECISION_ENGINE_CONFIG
    
    def calculate_question_score(
        self,
        is_correct: bool,
        difficulty: DifficultyLevel,
        hints_used: int
    ) -> QuestionScore:
        """
        Calculate score for a single question using weighted formula.
        
        Args:
            is_correct: Whether the answer was correct
            difficulty: Difficulty level of the question
            hints_used: Number of hints used
            
        Returns:
            QuestionScore object with components and final score
        """
        # Base score: 1.0 for correct, 0.0 for incorrect
        base = 1.0 if is_correct else 0.0
        
        # Difficulty multiplier
        difficulty_multiplier = self.config["difficulty_multipliers"].get(
            difficulty.value, 1.0
        )
        
        # Hint penalty
        hint_penalty = self.config["hint_penalties"].get(hints_used, 0.2)
        if hints_used > 2:
            hint_penalty = 0.2  # 2+ hints = 0.2 penalty
        
        return QuestionScore(
            base=base,
            difficulty_multiplier=difficulty_multiplier,
            hint_penalty=hint_penalty
        )
    
    def calculate_average_score(self, scores: List[QuestionScore]) -> float:
        """
        Calculate average score over multiple questions.
        
        Formula: S = (1/n) × Σ(Score_i)
        
        Args:
            scores: List of QuestionScore objects
            
        Returns:
            Average score (0-1)
        """
        if not scores:
            return 0.0
        
        total = sum(score.score for score in scores)
        return total / len(scores)
    
    def calculate_mastery(self, accuracy: float, consistency: float) -> float:
        """
        Calculate mastery score combining accuracy and consistency.
        
        Mastery = Accuracy × Consistency
        
        Args:
            accuracy: Accuracy percentage (0-100)
            consistency: Consistency factor (0-1), based on variance
            
        Returns:
            Mastery score (0-100)
        """
        # Normalize accuracy to 0-1
        normalized_accuracy = accuracy / 100.0
        return (normalized_accuracy * consistency) * 100
    
    def determine_mastery_status(self, mastery_score: float) -> MasteryStatus:
        """
        Determine mastery status based on mastery score.
        
        Args:
            mastery_score: Mastery score (0-100)
            
        Returns:
            MasteryStatus enum
        """
        if mastery_score > self.decision_config["mastery_high_threshold"] * 100:
            return MasteryStatus.PROFICIENT
        elif mastery_score < self.decision_config["mastery_low_threshold"] * 100:
            return MasteryStatus.STRUGGLING
        else:
            return MasteryStatus.LEARNING
    
    def calculate_consistency(self, recent_results: List[bool]) -> float:
        """
        Calculate consistency based on recent question results.
        
        Consistency is high when results are consistent (all correct or all incorrect)
        Low when results vary (mix of correct/incorrect)
        
        Args:
            recent_results: List of booleans (True=correct, False=incorrect)
            
        Returns:
            Consistency factor (0-1)
        """
        if len(recent_results) < 2:
            return 0.5  # No consistency data yet
        
        # Calculate variance
        correct_count = sum(recent_results)
        incorrect_count = len(recent_results) - correct_count
        
        # If all same, consistency is 1.0
        if incorrect_count == 0 or correct_count == 0:
            return 1.0
        
        # Otherwise, measure consistency as opposite of variance
        variance = (correct_count * incorrect_count) / (len(recent_results) ** 2)
        consistency = 1.0 - variance
        
        return consistency
    
    def get_window_scores(
        self,
        user_answers: List[UserAnswer],
        exercises_data: dict
    ) -> List[QuestionScore]:
        """
        Get scores for questions in the current mastery window.
        
        Args:
            user_answers: List of UserAnswer objects (should be sorted by timestamp)
            exercises_data: Dictionary mapping exercise_id to Exercise objects
            
        Returns:
            List of QuestionScore objects for the window
        """
        window_size = self.config["mastery_window"]
        
        # Get last N answers
        relevant_answers = user_answers[-window_size:] if len(user_answers) >= window_size else user_answers
        
        scores = []
        for answer in relevant_answers:
            exercise_id = answer.exercise_id
            if exercise_id in exercises_data:
                exercise = exercises_data[exercise_id]
                score = self.calculate_question_score(
                    is_correct=answer.is_correct,
                    difficulty=exercise.difficulty,
                    hints_used=answer.hints_used
                )
                scores.append(score)
        
        return scores
    
    def update_topic_performance(
        self,
        topic_performance: TopicPerformance,
        new_answer: UserAnswer,
        exercise: 'Exercise',
        all_topic_answers: List[UserAnswer],
        response_times: List[float]
    ) -> TopicPerformance:
        """
        Update topic performance with a new answer.
        
        Args:
            topic_performance: Current TopicPerformance object
            new_answer: New UserAnswer object
            exercise: Exercise object
            all_topic_answers: All answers for this topic
            response_times: All response times for this topic
            
        Returns:
            Updated TopicPerformance object
        """
        # Update question counts
        topic_performance.questions_answered += 1
        if new_answer.is_correct:
            topic_performance.questions_correct += 1
        
        # Calculate score for this question
        question_score = self.calculate_question_score(
            is_correct=new_answer.is_correct,
            difficulty=exercise.difficulty,
            hints_used=new_answer.hints_used
        )
        
        # Add to recent scores
        topic_performance.recent_scores.append(question_score.score)
        
        # Keep only last N scores (mastery window)
        window_size = self.config["mastery_window"]
        if len(topic_performance.recent_scores) > window_size:
            topic_performance.recent_scores = topic_performance.recent_scores[-window_size:]
        
        # Update average response time
        if response_times:
            topic_performance.average_response_time = sum(response_times) / len(response_times)
        
        # Calculate accuracy
        accuracy = (topic_performance.questions_correct / topic_performance.questions_answered) * 100
        
        # Calculate consistency
        recent_results = [answer.is_correct for answer in all_topic_answers[-window_size:]]
        consistency = self.calculate_consistency(recent_results)
        
        # Calculate mastery score
        topic_performance.mastery_score = self.calculate_mastery(accuracy, consistency)
        
        # Determine mastery status
        topic_performance.mastery_status = self.determine_mastery_status(topic_performance.mastery_score)
        
        # Calculate confidence level
        topic_performance.confidence_level = self._calculate_confidence_level(
            topic_performance.mastery_score,
            len(topic_performance.recent_scores)
        )
        
        return topic_performance
    
    def _calculate_confidence_level(self, mastery_score: float, sample_size: int) -> str:
        """
        Determine confidence level based on mastery score and sample size.
        
        Args:
            mastery_score: Current mastery score (0-100)
            sample_size: Number of recent questions
            
        Returns:
            Confidence level: "low", "medium", or "high"
        """
        # Need minimum questions before having confidence
        if sample_size < self.decision_config["min_questions_for_mastery"]:
            return "low"
        
        if mastery_score > 75:
            return "high"
        elif mastery_score > 40:
            return "medium"
        else:
            return "low"


# Global scoring engine instance
scoring_engine = ScoringEngine()
