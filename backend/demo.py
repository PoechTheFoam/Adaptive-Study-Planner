"""
Demonstration and testing utility for Scoring & Decision Engine

Shows how the adaptive learning algorithms work independent of the API.
Run with: python demo.py
"""
from models import (
    DifficultyLevel, TopicPerformance, UserAnswer, Exercise,
    MasteryStatus
)
from scoring import scoring_engine
from decision_engine import decision_engine
from datetime import datetime


def demo_scoring():
    """Demonstrate the scoring system"""
    print("\n" + "="*70)
    print("📊 SCORING SYSTEM DEMONSTRATION")
    print("="*70)
    
    print("""
The scoring formula is:
    Score = Base × Difficulty × HintPenalty
    
Where:
    Base = 1.0 (correct) or 0.0 (incorrect)
    Difficulty = 0.8 (easy), 1.0 (medium), 1.2 (hard)
    HintPenalty = 1.0 (no hints), 0.6 (1 hint), 0.2 (2+ hints)
    """)
    
    print("\n📝 EXAMPLES:")
    print("-" * 70)
    
    # Example 1: Correct, no hints, medium difficulty
    print("\n1️⃣  Correct answer, Medium difficulty, NO hints:")
    score1 = scoring_engine.calculate_question_score(
        is_correct=True,
        difficulty=DifficultyLevel.MEDIUM,
        hints_used=0
    )
    print(f"   Base: {score1.base}")
    print(f"   Difficulty Multiplier: {score1.difficulty_multiplier}")
    print(f"   Hint Penalty: {score1.hint_penalty}")
    print(f"   ✅ SCORE: {score1.score:.2f}")
    
    # Example 2: Correct, 1 hint, hard difficulty
    print("\n2️⃣  Correct answer, Hard difficulty, 1 hint used:")
    score2 = scoring_engine.calculate_question_score(
        is_correct=True,
        difficulty=DifficultyLevel.HARD,
        hints_used=1
    )
    print(f"   Base: {score2.base}")
    print(f"   Difficulty Multiplier: {score2.difficulty_multiplier}")
    print(f"   Hint Penalty: {score2.hint_penalty}")
    print(f"   ✅ SCORE: {score2.score:.2f}")
    
    # Example 3: Incorrect
    print("\n3️⃣  Incorrect answer, Easy difficulty:")
    score3 = scoring_engine.calculate_question_score(
        is_correct=False,
        difficulty=DifficultyLevel.EASY,
        hints_used=0
    )
    print(f"   Base: {score3.base}")
    print(f"   ❌ SCORE: {score3.score:.2f}")
    
    # Example 4: Correct, 2+ hints, easy
    print("\n4️⃣  Correct answer, Easy difficulty, 2+ hints:")
    score4 = scoring_engine.calculate_question_score(
        is_correct=True,
        difficulty=DifficultyLevel.EASY,
        hints_used=2
    )
    print(f"   Base: {score4.base}")
    print(f"   Difficulty Multiplier: {score4.difficulty_multiplier}")
    print(f"   Hint Penalty: {score4.hint_penalty}")
    print(f"   ⚠️  SCORE: {score4.score:.2f} (Mastery is low due to heavy hint use)")
    
    # Comparison
    print("\n📊 SCORE COMPARISON:")
    print("-" * 70)
    print(f"Example 1 (Correct, no hints, medium):    {score1.score:.2f}")
    print(f"Example 2 (Correct, 1 hint, hard):        {score2.score:.2f}")
    print(f"Example 3 (Incorrect):                    {score3.score:.2f}")
    print(f"Example 4 (Correct, 2+ hints, easy):      {score4.score:.2f}")
    print("\n💡 Hard with hints can still score higher than easy with heavy hints!")


def demo_mastery():
    """Demonstrate mastery calculation"""
    print("\n" + "="*70)
    print("🎯 MASTERY CALCULATION DEMONSTRATION")
    print("="*70)
    
    print("""
Mastery combines:
    1. Accuracy: How many questions correct (%)
    2. Consistency: How stable the performance is (0-1)
    
Formula: Mastery = (Accuracy / 100) × Consistency × 100
    """)
    
    print("\n📝 EXAMPLES:")
    print("-" * 70)
    
    # Example 1: All correct
    print("\n1️⃣  All correct answers (3/3):")
    consistency1 = scoring_engine.calculate_consistency([True, True, True])
    accuracy1 = 100.0
    mastery1 = scoring_engine.calculate_mastery(accuracy1, consistency1)
    status1 = scoring_engine.determine_mastery_status(mastery1)
    print(f"   Accuracy: {accuracy1:.1f}%")
    print(f"   Consistency: {consistency1:.2f}")
    print(f"   Mastery Score: {mastery1:.1f}%")
    print(f"   Status: {status1.value} ✅")
    
    # Example 2: Mixed results
    print("\n2️⃣  Mixed results (2 correct, 1 incorrect):")
    consistency2 = scoring_engine.calculate_consistency([True, True, False])
    accuracy2 = (2/3) * 100
    mastery2 = scoring_engine.calculate_mastery(accuracy2, consistency2)
    status2 = scoring_engine.determine_mastery_status(mastery2)
    print(f"   Accuracy: {accuracy2:.1f}%")
    print(f"   Consistency: {consistency2:.2f}")
    print(f"   Mastery Score: {mastery2:.1f}%")
    print(f"   Status: {status2.value} ⚠️")
    
    # Example 3: Inconsistent
    print("\n3️⃣  Very inconsistent (alternating correct/incorrect):")
    consistency3 = scoring_engine.calculate_consistency([True, False, True, False])
    accuracy3 = 50.0
    mastery3 = scoring_engine.calculate_mastery(accuracy3, consistency3)
    status3 = scoring_engine.determine_mastery_status(mastery3)
    print(f"   Accuracy: {accuracy3:.1f}%")
    print(f"   Consistency: {consistency3:.2f}")
    print(f"   Mastery Score: {mastery3:.1f}%")
    print(f"   Status: {status3.value} ❌")
    print(f"   💡 Unstable knowledge - can't rely on it!")
    
    # Example 4: All incorrect
    print("\n4️⃣  All incorrect (0/3):")
    consistency4 = scoring_engine.calculate_consistency([False, False, False])
    accuracy4 = 0.0
    mastery4 = scoring_engine.calculate_mastery(accuracy4, consistency4)
    status4 = scoring_engine.determine_mastery_status(mastery4)
    print(f"   Accuracy: {accuracy4:.1f}%")
    print(f"   Consistency: {consistency4:.2f}")
    print(f"   Mastery Score: {mastery4:.1f}%")
    print(f"   Status: {status4.value} ❌")


def demo_decision_engine():
    """Demonstrate the decision engine (AI brain)"""
    print("\n" + "="*70)
    print("🤖 DECISION ENGINE DEMONSTRATION")
    print("="*70)
    
    print("""
The Decision Engine decides what to do next based on:
    1. Current mastery level (0-100%)
    2. Consistency of performance
    3. Response time
    4. Current topic and difficulty
    
Decision Rules:
    Mastery > 85%:  ⬆️  INCREASE difficulty → Advance topic
    50% < Mastery < 85%: ➡️  KEEP same difficulty
    Mastery < 50%:  ⬇️  DECREASE difficulty → Review mode
    Response Time 2x+: ⬇️  Lower difficulty → Too slow
    """)
    
    print("\n📝 EXAMPLES:")
    print("-" * 70)
    
    # Example 1: Excellent performance
    print("\n1️⃣  Excellent performance (90% mastery):")
    topic_perf1 = TopicPerformance(
        topic="trigonometry",
        questions_answered=5,
        questions_correct=5,
        mastery_score=90.0,
        mastery_status=MasteryStatus.PROFICIENT,
        average_response_time=15.0
    )
    
    decision1 = decision_engine.decide_next_action(
        topic_performance=topic_perf1,
        current_topic="trigonometry",
        current_difficulty=DifficultyLevel.MEDIUM,
        recent_answers=[],
        exercises={},
        all_topics=["algebra", "trigonometry", "calculus"]
    )
    
    print(f"   Action: {decision1.action}")
    print(f"   New Difficulty: {decision1.recommended_difficulty.value}")
    print(f"   Reason: {decision1.reason}")
    print(f"   Feedback: {decision1.feedback}")
    
    # Example 2: Struggling
    print("\n2️⃣  Struggling (30% mastery):")
    topic_perf2 = TopicPerformance(
        topic="calculus",
        questions_answered=5,
        questions_correct=1,
        mastery_score=30.0,
        mastery_status=MasteryStatus.STRUGGLING,
        average_response_time=45.0
    )
    
    decision2 = decision_engine.decide_next_action(
        topic_performance=topic_perf2,
        current_topic="calculus",
        current_difficulty=DifficultyLevel.HARD,
        recent_answers=[],
        exercises={},
        all_topics=["algebra", "trigonometry", "calculus"]
    )
    
    print(f"   Action: {decision2.action}")
    print(f"   New Difficulty: {decision2.recommended_difficulty.value}")
    print(f"   Should Give Hints: {decision2.should_give_hint}")
    print(f"   Should Review: {decision2.should_review}")
    print(f"   Feedback: {decision2.feedback}")
    
    # Example 3: Good progress
    print("\n3️⃣  Steady progress (65% mastery):")
    topic_perf3 = TopicPerformance(
        topic="algebra",
        questions_answered=4,
        questions_correct=3,
        mastery_score=65.0,
        mastery_status=MasteryStatus.LEARNING,
        average_response_time=20.0
    )
    
    decision3 = decision_engine.decide_next_action(
        topic_performance=topic_perf3,
        current_topic="algebra",
        current_difficulty=DifficultyLevel.MEDIUM,
        recent_answers=[],
        exercises={},
        all_topics=["algebra", "trigonometry", "calculus"]
    )
    
    print(f"   Action: {decision3.action}")
    print(f"   Difficulty: {decision3.recommended_difficulty.value} (unchanged)")
    print(f"   Reason: {decision3.reason}")
    print(f"   Feedback: {decision3.feedback}")


def demo_adaptive_flow():
    """Demonstrate a complete adaptive learning flow"""
    print("\n" + "="*70)
    print("🎓 COMPLETE ADAPTIVE LEARNING FLOW")
    print("="*70)
    
    print("""
This shows how a student's experience changes as they improve:
    """)
    
    scenarios = [
        {
            "step": 1,
            "description": "Student starts (no data yet)",
            "difficulty": DifficultyLevel.MEDIUM,
            "accuracy": 0.0,
            "decision": "Start with medium difficulty"
        },
        {
            "step": 2,
            "description": "Student answers 3 questions: ❌❌✅",
            "answers": [False, False, True],
            "accuracy": 33.3,
            "mastery": 16.7,
            "decision": "Lower difficulty - struggling"
        },
        {
            "step": 3,
            "description": "More practice at EASY: ✅✅✅",
            "answers": [True, True, True],
            "accuracy": 100.0,
            "mastery": 100.0,
            "decision": "Perfect! Increase difficulty"
        },
        {
            "step": 4,
            "description": "Try MEDIUM again: ✅✅❌",
            "answers": [True, True, False],
            "accuracy": 66.7,
            "mastery": 66.7,
            "decision": "Good progress, keep going"
        },
        {
            "step": 5,
            "description": "More MEDIUM: ✅✅✅✅✅",
            "answers": [True, True, True, True, True],
            "accuracy": 80.0,
            "mastery": 80.0,
            "decision": "Strong mastery! Try HARD"
        },
    ]
    
    for scenario in scenarios:
        print(f"\n{'='*70}")
        print(f"Step {scenario['step']}: {scenario['description']}")
        print('-' * 70)
        
        if 'answers' in scenario:
            answers = scenario['answers']
            accuracy = (sum(answers) / len(answers)) * 100
            consistency = scoring_engine.calculate_consistency(answers)
            mastery = scoring_engine.calculate_mastery(accuracy, consistency)
            status = scoring_engine.determine_mastery_status(mastery)
            
            print(f"Accuracy: {accuracy:.1f}%")
            print(f"Consistency: {consistency:.2f}")
            print(f"Mastery: {mastery:.1f}%")
            print(f"Status: {status.value}")
        
        print(f"\n✅ Decision: {scenario['decision']}")


def main():
    """Run all demonstrations"""
    print("\n" + "="*70)
    print("🎓 ADAPTIVE LEARNING PLATFORM - DEMO")
    print("="*70)
    print("""
This script demonstrates the core algorithms of the adaptive learning
platform without needing a server or API key.
    """)
    
    # Run demos
    demo_scoring()
    demo_mastery()
    demo_decision_engine()
    demo_adaptive_flow()
    
    # Summary
    print("\n" + "="*70)
    print("✅ DEMONSTRATION COMPLETE")
    print("="*70)
    print("""
Key Takeaways:

1. 📊 SCORING: Rewards correct answers + skill difficulty - hint penalty
   
2. 🎯 MASTERY: Combines accuracy + consistency over time
   
3. 🤖 DECISION ENGINE: Autom automatically adjusts based on performance
   - High mastery → Harder problems
   - Low mastery → Easier problems  
   - Hints when struggling
   
4. 🎓 ADAPTIVE FLOW: Students learn at their own pace
   - Get immediate feedback
   - Questions adapt to skill level
   - Confidence grows with consistent success

For full API documentation, see README.md and visit:
   http://127.0.0.1:8000/docs (after starting the server)
    """)


if __name__ == "__main__":
    main()
