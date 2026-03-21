# 🎓 Adaptive Learning Platform - Backend

A sophisticated AI-powered adaptive learning system that intelligently adjusts learning difficulty based on user performance using Google's Gemini API.

## 🏗️ Architecture

```
Input Layer (User Topics/Skills)
         ↓
Content Engine (Gemini-powered Question Generation)
         ↓
Evaluation Engine (Scoring & Tracking)
         ↓
Decision Engine (AI Brain - Adaptive Logic)
         ↓
Feedback Loop (Update User Profile)
```

## 📊 Scoring System

**Weighted Score Formula:**
```
Score = (1/n) × Σ(Base × Difficulty × HintPenalty)
```

### Components:
- **Base**: 1.0 (correct) / 0.0 (incorrect)
- **Difficulty Multiplier**: 
  - Easy: 0.8
  - Medium: 1.0
  - Hard: 1.2
- **Hint Penalty**:
  - No hints: 1.0
  - 1 hint: 0.6
  - 2+ hints: 0.2

### Mastery Logic:
- **Mastery > 85%**: Increase difficulty + Advance to next topic
- **Mastery < 50%**: Review mode + Lower difficulty
- **Response Time > 2x Average**: Flag as struggling

## 🎯 Decision Engine

The "AI Brain" makes adaptive decisions:

1. **Performance-based difficulty adjustment**
2. **Hint/explanation provision**
3. **Topic progression**
4. **Review vs. advance decisions**

## 🔧 Tech Stack

- **Framework**: FastAPI
- **Database**: SQLite
- **AI/LLM**: Google Gemini API
- **Language**: Python 3.8+

## ⚡ Quick Start

### 1. Setup Environment

```bash
# Clone/Navigate to project
cd backend1

# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. ⚠️ **IMPORTANT: Configure API Key**

#### Option A: Using .env file (Recommended)
```bash
# Copy example to .env
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your_actual_api_key_here
```

#### Option B: Direct in config.py
Edit `config.py`:
```python
GEMINI_API_KEY = "your_api_key_here"
```

### Get Your Gemini API Key:
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikeys)
2. Click "Get API key"
3. Create new API key
4. Copy and paste into .env or config.py

### 3. Run the Server

```bash
# From the backend1 directory
python main.py
```

Server will start at: **http://127.0.0.1:8000**

### 4. Access API Documentation

- **Interactive Docs**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 📡 API Endpoints

### User Management

#### Create User
```http
POST /user/create
Content-Type: application/json

{
  "name": "John Doe",
  "skill_level": "beginner",
  "goal": "mastery",
  "initial_topic": "algebra"
}
```

**Response:**
```json
{
  "user_id": "uuid",
  "name": "John Doe",
  "skill_level": "beginner",
  "goal": "mastery",
  "current_topic": "algebra",
  "current_difficulty": "medium",
  "overall_mastery": 0.0,
  "total_questions_answered": 0
}
```

#### Get User Profile
```http
GET /user/profile?user_id=<user_id>
```

#### Get User Progress
```http
GET /user/progress?user_id=<user_id>
```

### Question & Answer Flow

#### Get Question
```http
POST /get_question
Content-Type: application/json

{
  "user_id": "uuid",
  "topic": "trigonometry"  // optional, uses current if null
}
```

**Response:**
```json
{
  "exercise_id": "uuid",
  "topic": "trigonometry",
  "difficulty": "medium",
  "question": "What is sin(π/6)?",
  "hints_available": 2
}
```

#### Get Hint
```http
POST /get_hint?user_id=<user_id>&exercise_id=<exercise_id>&hint_number=1
```

**Response:**
```json
{
  "hint": "Remember: π/6 is 30 degrees",
  "hint_number": 1,
  "exercise_id": "uuid"
}
```

#### Submit Answer
```http
POST /submit_answer
Content-Type: application/json

{
  "user_id": "uuid",
  "exercise_id": "uuid",
  "user_answer": "0.5",
  "response_time": 25.5,
  "hints_used": 1
}
```

**Response:**
```json
{
  "is_correct": true,
  "explanation": "sin(π/6) = 0.5. π/6 radians = 30°, and sin(30°) = 1/2.",
  "mastery_score": 72.5,
  "feedback": "✅ Correct! Great job on this medium question!",
  "should_give_hint": false
}
```

### Decision Engine

#### Get Next Action
```http
POST /next_action?user_id=<user_id>
```

**Response:**
```json
{
  "action": "next_question",
  "recommended_difficulty": "hard",
  "recommended_topic": "trigonometry",
  "reason": "Excellent! Mastery 87.5% - Time to advance.",
  "feedback": "🎉 Great job! You've mastered trigonometry. Moving to harder problems!"
}
```

### Utility Endpoints

#### Get Available Topics
```http
GET /topics
```

#### Get Questions by Difficulty
```http
GET /questions/by-difficulty?topic=algebra&difficulty=medium
```

#### Health Check
```http
GET /health
```

## 📁 Project Structure

```
backend1/
├── config.py                    # Configuration & API keys
├── models.py                    # Data models & enums
├── scoring.py                   # Scoring engine & mastery calculation
├── decision_engine.py           # AI brain for adaptive decisions
├── gemini_integration.py        # Gemini API integration
├── database.py                  # SQLite operations & CRUD
├── main.py                      # FastAPI application & endpoints
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .env                         # Environment variables (YOUR API KEY)
├── adaptive_learning.db         # SQLite database (auto-created)
└── README.md                    # This file
```

## 🧠 Scoring & Mastery System

### Score Calculation Example:

**Scenario**: User answers "hard" question correctly with 1 hint

```
Base = 1.0 (correct)
Difficulty = 1.2 (hard)
HintPenalty = 0.6 (1 hint used)

Score = 1.0 × 1.2 × 0.6 = 0.72
```

### Mastery Window:
- Calculated over last 3 questions
- Accounts for consistency & accuracy
- Prevents overreaction to single questions

### Confidence Levels:
- **Low**: < 3 questions or < 40% mastery
- **Medium**: 40-75% mastery
- **High**: > 75% mastery

## 🤖 Decision Engine Rules

The decision engine evaluates:

1. **Mastery Status**
   - `PROFICIENT` (>85%): Increase difficulty
   - `LEARNING` (50-85%): Continue current level
   - `STRUGGLING` (<50%): Review with hints
   - `UNSTABLE`: Inconsistent performance

2. **Time-based Adjustments**
   - If response_time > 2× average: Lower difficulty

3. **Actions**
   - `next_question`: Continue with current settings
   - `advance`: Move to harder problems/next topic
   - `review`: Review concept with lower difficulty
   - `explain`: Provide detailed explanation

## 📝 Data Models

### UserProfile
```python
- user_id: str
- name: str
- skill_level: beginner | intermediate | advanced
- goal: exam | mastery | speed
- current_topic: str
- current_difficulty: easy | medium | hard
- overall_mastery: float (0-100)
- average_response_time: float
```

### Exercise
```python
- exercise_id: str
- topic: str
- difficulty: easy | medium | hard
- question: str
- answer: str
- explanation: str
- hints: List[str]
```

### TopicPerformance
```python
- topic: str
- questions_answered: int
- questions_correct: int
- mastery_score: float (0-100)
- mastery_status: struggling | learning | proficient | unstable
- average_response_time: float
- confidence_level: low | medium | high
```

## 🔌 Gemini API Integration

The system uses Gemini API for:
- **Question Generation**: Creates contextual problems
- **Hint Generation**: Provides progressive hints
- **Explanation Generation**: Explains solutions

### Fallback Mechanism:
If API unavailable, returns dummy questions for development/testing.

## 📊 Database Schema

### Tables:
1. **users** - User profiles and preferences
2. **exercises** - Questions and solutions
3. **user_answers** - Answer submissions and scoring
4. **topic_performance** - Mastery tracking per topic

## 🚀 Deployment Tips

### For Production:
1. Use environment variables (not hardcoded keys)
2. Add authentication (JWT tokens)
3. Use PostgreSQL instead of SQLite
4. Add rate limiting
5. Use HTTPS
6. Add logging and monitoring
7. Cache questions in Redis

### Example Production Setup:
```bash
# Using Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

## 🧪 Testing

```bash
# Run tests
pytest -v

# With coverage
pytest --cov=. -v
```

## 📚 Example Workflow

```python
# 1. Create user
POST /user/create
→ Returns user_id

# 2. Get question
POST /get_question
→ Returns exercise_id and question

# 3. User solves (frontend)
# (user thinks about answer)

# 4. Submit answer
POST /submit_answer
→ Returns is_correct, explanation, mastery_score

# 5. Check next action
POST /next_action
→ Returns recommended difficulty, topic, action

# Repeat 2-5 for adaptive learning!
```

## 🛠️ Troubleshooting

### API Key Issues
```
Error: "GEMINI_API_KEY not set"
→ Add your key to .env or config.py
```

### Database Issues
```
Error: "sqlite3.OperationalError"
→ Delete adaptive_learning.db and restart
```

### Port Already in Use
```
Error: "Address already in use"
→ Change port in main.py or kill process on 8000
```

## 📈 Future Enhancements

- [ ] User authentication (JWT)
- [ ] Question bank management
- [ ] Analytics dashboard
- [ ] Spaced repetition algorithm
- [ ] Collaborative learning features
- [ ] Multi-language support
- [ ] Mobile app integration
- [ ] Advanced metrics & analytics

## 📄 License

MIT License - Feel free to use for hackathons and personal projects!

## 🤝 Contributing

Found a bug? Have a feature idea? Create an issue or PR!

## 📞 Support

For issues with:
- **Gemini API**: See [Google AI Documentation](https://ai.google.dev/)
- **FastAPI**: See [FastAPI Documentation](https://fastapi.tiangolo.com/)
- **This Project**: Check `.env` setup and verify API key

---

**Happy Learning! 🎓**

Made with ❤️ for hackathons and adaptive learning systems.
