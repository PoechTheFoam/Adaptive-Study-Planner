"""
Adaptive Learning Platform - FastAPI Backend

Main application with endpoints:
- /get_question
- /submit_answer
- /next_action
- /user/profile
- /user/progress
- /health
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import time

from models import (
    UserProfile, Exercise, UserAnswer, DifficultyLevel, 
    SkillLevel, Goal, TopicPerformance
)
from database import db
from scoring import scoring_engine
from decision_engine import decision_engine
from gemini_integration import gemini_client
from config import TOPICS, DIFFICULTY_LEVELS, SKILL_LEVELS, GOALS

# ============================================================================
# IMPORTANT REMINDER: Add your GEMINI_API_KEY to config.py!
# ============================================================================

# FastAPI app setup
app = FastAPI(
    title="Adaptive Learning Platform Backend",
    description="AI-powered adaptive learning system with Gemini integration",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================

class CreateUserRequest(BaseModel):
    """Request to create a new user"""
    name: str
    skill_level: str  # beginner, intermediate, advanced
    goal: str  # exam, mastery, speed
    initial_topic: str


class GetQuestionRequest(BaseModel):
    """Request to get a question"""
    user_id: str
    topic: Optional[str] = None  # If None, use current topic


class SubmitAnswerRequest(BaseModel):
    """Request to submit an answer"""
    user_id: str
    exercise_id: str
    user_answer: str
    user_reasoning:str
    response_time: float  # seconds
    hints_used: int = 0


class QuestionResponse(BaseModel):
    """Response containing a question"""
    exercise_id: str
    topic: str
    difficulty: str
    question: str
    hints_available: int = 2


class AnswerSubmissionResponse(BaseModel):
    """Response after submitting an answer"""
    is_correct: bool
    explanation: str
    mastery_score: float
    feedback: str
    should_give_hint: bool


class NextActionResponse(BaseModel):
    """Response with next action recommendation"""
    action: str
    recommended_difficulty: str
    recommended_topic: str
    reason: str
    feedback: str


class UserProfileResponse(BaseModel):
    """User profile response"""
    user_id: str
    name: str
    skill_level: str
    goal: str
    current_topic: str
    current_difficulty: str
    overall_mastery: float
    total_questions_answered: int


class UserProgressResponse(BaseModel):
    """User progress across topics"""
    user_id: str
    overall_mastery: float
    topics: List[dict]


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "Adaptive Learning Platform Backend is running"
    }


@app.post("/user/create", response_model=UserProfileResponse)
async def create_user(request: CreateUserRequest):
    """
    Create a new user.
    
    Args:
        name: User's name
        skill_level: beginner, intermediate, or advanced
        goal: exam, mastery, or speed
        initial_topic: Starting topic
    """
    
    # Validate inputs
    if request.skill_level not in SKILL_LEVELS:
        raise HTTPException(status_code=400, detail=f"Invalid skill level: {request.skill_level}")
    if request.goal not in GOALS:
        raise HTTPException(status_code=400, detail=f"Invalid goal: {request.goal}")
    if request.initial_topic not in TOPICS:
        raise HTTPException(status_code=400, detail=f"Invalid topic: {request.initial_topic}")
    
    # Create user
    user_id = str(uuid.uuid4())
    user = UserProfile(
        user_id=user_id,
        name=request.name,
        skill_level=SkillLevel(request.skill_level),
        goal=Goal(request.goal),
        current_topic=request.initial_topic,
        current_difficulty=DifficultyLevel.MEDIUM
    )
    
    # Save to database
    if not db.create_user(user):
        raise HTTPException(status_code=500, detail="Failed to create user")
    
    # Initialize topic performance
    perf = TopicPerformance(topic=request.initial_topic)
    db.save_topic_performance(user_id, perf)
    
    return UserProfileResponse(
        user_id=user.user_id,
        name=user.name,
        skill_level=user.skill_level.value,
        goal=user.goal.value,
        current_topic=user.current_topic,
        current_difficulty=user.current_difficulty.value,
        overall_mastery=user.overall_mastery,
        total_questions_answered=user.total_questions_answered
    )


@app.post("/get_question", response_model=QuestionResponse)
async def get_question(request: GetQuestionRequest):
    """
    Get a question for the user.
    
    Returns a question based on user's current level and topic.
    """
    
    # Get user
    user = db.get_user(request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Determine topic
    topic = request.topic if request.topic else user.current_topic
    if not topic:
        raise HTTPException(status_code=400, detail="No topic specified")
    
    # Get current difficulty
    difficulty = user.current_difficulty
    
    # Try to get exercise from database
    exercises = db.get_exercises_by_topic_difficulty(topic, difficulty)
    
    if exercises:
        # Pick a random exercise from database
        exercise = exercises[0]  # In production, randomize
    else:
        # Generate new exercise using Gemini
        print(f"📝 Generating new question for {topic} ({difficulty.value})...")
        
        gen_data = gemini_client.generate_question(
            topic=topic,
            difficulty=difficulty,
            skill_level=user.skill_level.value,
            goal=user.goal.value
        )
        
        if not gen_data:
            raise HTTPException(status_code=500, detail="Failed to generate question")
        
        # Create exercise object
        exercise_id = str(uuid.uuid4())
        exercise = Exercise(
            exercise_id=exercise_id,
            topic=topic,
            difficulty=difficulty,
            question=gen_data["question"],
            answer=gen_data["answer"],
            explanation=gen_data["explanation"],
            hints=gen_data.get("hints", [])
        )
        
        # Save to database for reuse
        db.create_exercise(exercise)
    
    return QuestionResponse(
        exercise_id=exercise.exercise_id,
        topic=exercise.topic,
        difficulty=exercise.difficulty.value,
        question=exercise.question,
        hints_available=len(exercise.hints)
    )


@app.post("/get_hint")
async def get_hint(user_id: str, exercise_id: str, hint_number: int = 1):
    """
    Get a hint for a question.
    
    Args:
        user_id: User ID
        exercise_id: Exercise ID
        hint_number: Which hint to get (1, 2, etc.)
    """
    
    # Get exercise
    exercise = db.get_exercise(exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    # Check if hint exists in database
    if hint_number <= len(exercise.hints):
        hint = exercise.hints[hint_number - 1]
    else:
        # Generate hint using Gemini
        hint = gemini_client.generate_hint(
            question=exercise.question,
            topic=exercise.topic,
            hint_number=hint_number
        )
    
    return {
        "hint": hint,
        "hint_number": hint_number,
        "exercise_id": exercise_id
    }


@app.post("/submit_answer", response_model=AnswerSubmissionResponse)
async def submit_answer(request: SubmitAnswerRequest):
    """
    Submit an answer to a question.
    
    Evaluates the answer, calculates score, and provides feedback.
    ⚠️  IMPORTANT: Make sure your GEMINI_API_KEY is set!
    """
    
    # Get user and exercise
    user = db.get_user(request.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    exercise = db.get_exercise(request.exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    
    # Check if answer is correct (case-insensitive for simple comparison)
    is_correct = request.user_answer.strip().lower() == exercise.answer.strip().lower()
    # Create user answer record
    user_answer = UserAnswer(
        user_id=request.user_id,
        exercise_id=request.exercise_id,
        user_answer=request.user_answer,
        is_correct=is_correct,
        response_time=request.response_time,
        hints_used=request.hints_used,
        conceptual_match=request.conceptual_match,
        understanding=request.understanding
    )

    result=gemini_client.evaluate_reasoning(exercise.question,exercise.answer,request.user_reasoning,exercise.topic)
    if result is None:
        result = {
            "concept_match": False,
            "understanding": "weak"
        }

    # Save answer
    db.save_answer(user_answer)
    
    # Calculate score
    question_score = scoring_engine.calculate_question_score(
        is_correct=is_correct,
        difficulty=exercise.difficulty,
        hints_used=request.hints_used
    )
    
    # Get all topic answers for mastery calculation
    topic_answers = db.get_user_answers_for_topic(request.user_id, exercise.topic)
    
    # Update topic performance
    topic_perf = db.get_topic_performance(request.user_id, exercise.topic)
    if not topic_perf:
        topic_perf = TopicPerformance(topic=exercise.topic)
    
    response_times = [ans.response_time for ans in topic_answers]
    topic_perf = scoring_engine.update_topic_performance(
        topic_perf, user_answer, exercise, topic_answers, response_times
    )
    
    db.save_topic_performance(request.user_id, topic_perf)
    
    # Update overall user mastery
    all_perfs = db.get_all_topic_performance(request.user_id)
    total_mastery = sum(p.mastery_score for p in all_perfs) / len(all_perfs) if all_perfs else 0
    user.overall_mastery = total_mastery
    
    # Generate explanation
    explanation = gemini_client.generate_explanation(
        question=exercise.question,
        correct_answer=exercise.answer,
        user_answer=request.user_answer if not is_correct else None
    )
    
    # Decide if should give hint
    should_give_hint = decision_engine.should_give_hint(
        hints_already_used=request.hints_used,
        mastery_score=topic_perf.mastery_score,
        question_difficulty=exercise.difficulty
    )
    
    # Generate feedback
    if is_correct:
        feedback = f"✅ Correct! Great job on this {exercise.difficulty.value} question!"
        if result["understanding"] == "strong":
            feedback += " Your reasoning is solid."
        else:
            feedback += " Your reasoning is weak."
        if question_score.score < 0.5:
            feedback += " (But you used hints - try without hints next time for full points)"
    else:
        feedback = f"❌ Incorrect. The correct answer is: {exercise.answer}"
    # Save updated user
    db.update_user(user)
    
    return AnswerSubmissionResponse(
        is_correct=is_correct,
        explanation=explanation,
        mastery_score=topic_perf.mastery_score,
        feedback=feedback,
        should_give_hint=should_give_hint
    )


@app.post("/next_action", response_model=NextActionResponse)
async def next_action(user_id: str):
    """
    Get the next recommended action for the user.
    
    Uses the decision engine to recommend:
    - Next difficulty level
    - Whether to review or advance
    - Next topic
    - Whether to provide hints
    """
    
    # Get user and performance data
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get current topic performance
    topic_perf = db.get_topic_performance(user_id, user.current_topic)
    if not topic_perf:
        topic_perf = TopicPerformance(topic=user.current_topic)
    
    # Get recent answers
    recent_answers = db.get_user_answers(user_id, limit=5)
    
    # Get decision from decision engine
    decision = decision_engine.decide_next_action(
        topic_performance=topic_perf,
        current_topic=user.current_topic,
        current_difficulty=user.current_difficulty,
        recent_answers=recent_answers,
        exercises={},  # Could load exercises if needed
        all_topics=TOPICS
    )
    
    # Update user if difficulty changed
    if decision.recommended_difficulty != user.current_difficulty:
        user.current_difficulty = decision.recommended_difficulty
        db.update_user(user)
    
    return NextActionResponse(
        action=decision.action,
        recommended_difficulty=decision.recommended_difficulty.value,
        recommended_topic=decision.recommended_topic,
        reason=decision.reason,
        feedback=decision.feedback
    )


@app.get("/user/profile", response_model=UserProfileResponse)
async def get_user_profile(user_id: str):
    """Get user profile"""
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserProfileResponse(
        user_id=user.user_id,
        name=user.name,
        skill_level=user.skill_level.value,
        goal=user.goal.value,
        current_topic=user.current_topic,
        current_difficulty=user.current_difficulty.value,
        overall_mastery=user.overall_mastery,
        total_questions_answered=user.total_questions_answered
    )


@app.get("/user/progress")
async def get_user_progress(user_id: str):
    """
    Get user's progress across all topics.
    """
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get performance for all topics
    all_perfs = db.get_all_topic_performance(user_id)
    
    topics_data = [p.to_dict() for p in all_perfs]
    
    return UserProgressResponse(
        user_id=user_id,
        overall_mastery=user.overall_mastery,
        topics=topics_data
    )


@app.get("/questions/by-difficulty")
async def get_questions_by_difficulty(topic: str, difficulty: str):
    """Get available questions by topic and difficulty"""
    try:
        diff_enum = DifficultyLevel(difficulty)
        exercises = db.get_exercises_by_topic_difficulty(topic, diff_enum)
        
        return {
            "topic": topic,
            "difficulty": difficulty,
            "count": len(exercises),
            "exercises": [{"exercise_id": e.exercise_id, "question": e.question} for e in exercises]
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid difficulty level")


@app.get("/topics")
async def get_topics():
    """Get list of available topics"""
    return {
        "topics": TOPICS,
        "count": len(TOPICS)
    }


@app.get("/")
async def root():
    """Root endpoint - API documentation"""
    return {
        "name": "Adaptive Learning Platform Backend",
        "version": "1.0.0",
        "description": "AI-powered adaptive learning system with Gemini integration",
        "endpoints": {
            "health": "GET /health",
            "create_user": "POST /user/create",
            "get_question": "POST /get_question",
            "get_hint": "POST /get_hint",
            "submit_answer": "POST /submit_answer",
            "next_action": "POST /next_action",
            "user_profile": "GET /user/profile",
            "user_progress": "GET /user/progress",
            "available_topics": "GET /topics",
            "questions_by_difficulty": "GET /questions/by-difficulty"
        },
        "important_reminder": "⚠️  MAKE SURE TO SET YOUR GEMINI_API_KEY IN config.py!"
    }


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    from config import GEMINI_API_KEY
    
    print("\n" + "="*70)
    print("🚀 Adaptive Learning Platform Backend")
    print("="*70)
    print(f"📝 Config file: config.py")
    api_status = "✅ Yes" if GEMINI_API_KEY else "❌ No"
    print(f"🔑 GEMINI_API_KEY set: {api_status}")
    print(f"💾 Database: adaptive_learning.db")
    print("\n🌐 Starting server on http://127.0.0.1:8000")
    print("📚 API Docs: http://127.0.0.1:8000/docs")
    print("="*70 + "\n")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
