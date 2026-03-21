"""
Decision Engine - The "AI Brain" of the Adaptive Learning Platform

Decides:
- Next question difficulty
- Whether to give hints/explanations
- Whether to review or advance topics
- Overall learning progression
"""
from typing import List, Dict, Optional
from models import (
    DifficultyLevel,
    MasteryStatus,
    TopicPerformance,
    NextActionDecision,
    UserAnswer,
    Exercise
)
from config import DECISION_ENGINE_CONFIG, DIFFICULTY_LEVELS
from scoring import scoring_engine


class DecisionEngine:
    """The AI brain that makes adaptive learning decisions"""
    
    def __init__(self):
        self.config = DECISION_ENGINE_CONFIG
    
    def decide_next_action(
        self,
        topic_performance: TopicPerformance,
        current_topic: str,
        current_difficulty: DifficultyLevel,
        recent_answers: List[UserAnswer],
        exercises: Dict[str, Exercise],
        all_topics: List[str]
    ) -> NextActionDecision:
        """
        Determine the next action the user should take.
        
        Decision logic:
        - Mastery > 85%: Increase difficulty & move to next sub-topic
        - Mastery < 50%: Trigger review mode & offer lower difficulty
        - Time > 2x average: Flag as struggling
        - Average mastery over 3-question window
        
        Args:
            topic_performance: Performance data for current topic
            current_topic: Current topic being studied
            current_difficulty: Current difficulty level
            recent_answers: Recent user answers
            exercises: Dictionary of all exercises
            all_topics: List of available topics
            
        Returns:
            NextActionDecision object
        """
        mastery_score = topic_performance.mastery_score
        mastery_status = topic_performance.mastery_status
        avg_time = topic_performance.average_response_time
        
        # Check if user is struggling with time
        is_struggling_with_time = self._is_struggling_with_time(recent_answers)
        
        # Main decision logic
        if mastery_status == MasteryStatus.PROFICIENT:
            return self._handle_proficient_performance(
                current_topic, current_difficulty, all_topics, mastery_score
            )
        elif mastery_status == MasteryStatus.STRUGGLING:
            return self._handle_struggling_performance(
                current_topic, current_difficulty, mastery_score
            )
        elif is_struggling_with_time and mastery_status != MasteryStatus.PROFICIENT:
            return self._handle_time_struggling(
                current_topic, current_difficulty, mastery_score
            )
        else:
            # Learning normally - continue with current difficulty
            return NextActionDecision(
                action="next_question",
                recommended_difficulty=current_difficulty,
                recommended_topic=current_topic,
                reason=f"Steady progress. Mastery: {mastery_score:.1f}% ({mastery_status.value})",
                feedback=f"Keep practicing this topic! You're making steady progress."
            )
    
    def _handle_proficient_performance(
        self,
        current_topic: str,
        current_difficulty: DifficultyLevel,
        all_topics: List[str],
        mastery_score: float
    ) -> NextActionDecision:
        """Handle case when mastery > 85% (proficient)"""
        
        # Increase difficulty if not already at max
        next_difficulty = self._increase_difficulty(current_difficulty)
        
        # Suggest next topic (if available)
        next_topic = self._get_next_topic(current_topic, all_topics)
        
        action = "advance" if next_difficulty == current_difficulty else "next_question"
        
        return NextActionDecision(
            action=action,
            recommended_difficulty=next_difficulty,
            recommended_topic=next_topic if next_difficulty == current_difficulty else current_topic,
            reason=f"Excellent! Mastery {mastery_score:.1f}% - Time to advance.",
            should_advance=True,
            feedback=f"🎉 Great job! You've mastered {current_topic}. "
                    f"Moving to harder problems or next topic!"
        )
    
    def _handle_struggling_performance(
        self,
        current_topic: str,
        current_difficulty: DifficultyLevel,
        mastery_score: float
    ) -> NextActionDecision:
        """Handle case when mastery < 50% (struggling)"""
        
        # Decrease difficulty
        next_difficulty = self._decrease_difficulty(current_difficulty)
        
        return NextActionDecision(
            action="review",
            recommended_difficulty=next_difficulty,
            recommended_topic=current_topic,
            reason=f"Mastery {mastery_score:.1f}% - Need review.",
            should_review=True,
            should_give_hint=True,
            feedback=f"Don't worry! Let's review {current_topic} at an easier level. "
                    f"I'll provide hints to help you."
        )
    
    def _handle_time_struggling(
        self,
        current_topic: str,
        current_difficulty: DifficultyLevel,
        mastery_score: float
    ) -> NextActionDecision:
        """Handle case when response time is too high"""
        
        # Decrease difficulty to reduce cognitive load
        next_difficulty = self._decrease_difficulty(current_difficulty)
        
        return NextActionDecision(
            action="next_question",
            recommended_difficulty=next_difficulty,
            recommended_topic=current_topic,
            reason=f"Taking too long per question. Adjusting difficulty.",
            should_give_hint=True,
            feedback=f"You're taking longer than usual. Let's practice {current_topic} "
                    f"at an easier pace with hints to speed up your processing."
        )
    
    def _is_struggling_with_time(self, recent_answers: List[UserAnswer]) -> bool:
        """
        Check if user is taking too long on questions.
        
        Flags as struggling if time > 2x of their average recent time.
        """
        if len(recent_answers) < 2:
            return False
        
        times = [answer.response_time for answer in recent_answers[-5:]]  # Last 5
        average = sum(times) / len(times)
        threshold = average * self.config["time_multiplier_threshold"]
        
        # If last answer took too long, flag it
        if recent_answers[-1].response_time > threshold:
            return True
        
        return False
    
    def _increase_difficulty(self, current: DifficultyLevel) -> DifficultyLevel:
        """Increase difficulty level"""
        difficulty_order = [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD]
        try:
            current_index = difficulty_order.index(current)
            if current_index < len(difficulty_order) - 1:
                return difficulty_order[current_index + 1]
        except (ValueError, IndexError):
            pass
        return current  # Already at max
    
    def _decrease_difficulty(self, current: DifficultyLevel) -> DifficultyLevel:
        """Decrease difficulty level"""
        difficulty_order = [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD]
        try:
            current_index = difficulty_order.index(current)
            if current_index > 0:
                return difficulty_order[current_index - 1]
        except (ValueError, IndexError):
            pass
        return current  # Already at min
    
    def _get_next_topic(
        self,
        current_topic: str,
        all_topics: List[str]
    ) -> str:
        """Get the next topic to study"""
        try:
            current_index = all_topics.index(current_topic)
            if current_index < len(all_topics) - 1:
                return all_topics[current_index + 1]
        except (ValueError, IndexError):
            pass
        return current_topic  # Stay on current topic
    
    def should_give_hint(
        self,
        hints_already_used: int,
        mastery_score: float,
        question_difficulty: DifficultyLevel
    ) -> bool:
        """
        Determine if user should receive a hint.
        
        Args:
            hints_already_used: Number of hints used for this question
            mastery_score: Current mastery score
            question_difficulty: Difficulty of current question
            
        Returns:
            Boolean indicating whether to offer hint
        """
        # Don't give more than 2 hints per question
        if hints_already_used >= 2:
            return False
        
        # Give hints more liberally to struggling students
        if mastery_score < self.config["mastery_low_threshold"] * 100:
            return True  # Always offer hints when struggling
        
        # For hard questions, offer one hint
        if question_difficulty == DifficultyLevel.HARD and hints_already_used == 0:
            return True
        
        return False
    
    def should_explain(
        self,
        is_correct: bool,
        mastery_score: float
    ) -> bool:
        """
        Determine if user should receive an explanation.
        
        Args:
            is_correct: Whether the answer was correct
            mastery_score: Current mastery score
            
        Returns:
            Boolean indicating whether to provide explanation
        """
        # Always explain wrong answers
        if not is_correct:
            return True
        
        # Explain correct answers for struggling students
        if mastery_score < self.config["mastery_low_threshold"] * 100:
            return True
        
        return False
    
    def get_adaptive_question_difficulty(
        self,
        user_current_difficulty: DifficultyLevel,
        mastery_by_difficulty: Dict[DifficultyLevel, float]
    ) -> DifficultyLevel:
        """
        Intelligently select next question difficulty based on user performance.
        
        Args:
            user_current_difficulty: Current difficulty level
            mastery_by_difficulty: Dict of mastery scores by difficulty
            
        Returns:
            Recommended difficulty for next question
        """
        thresholds = self.config
        
        # If high mastery at current level, recommend higher
        if mastery_by_difficulty.get(user_current_difficulty, 0) > thresholds["mastery_high_threshold"] * 100:
            return self._increase_difficulty(user_current_difficulty)
        
        # If low mastery at current level, recommend lower
        if mastery_by_difficulty.get(user_current_difficulty, 0) < thresholds["mastery_low_threshold"] * 100:
            return self._decrease_difficulty(user_current_difficulty)
        
        # Otherwise stay at current
        return user_current_difficulty


# Global decision engine instance
decision_engine = DecisionEngine()
