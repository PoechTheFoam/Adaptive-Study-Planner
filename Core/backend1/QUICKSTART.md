# 🚀 QUICK START GUIDE

## For Hackathon: Adaptive Learning Platform Backend

### ⏱️ 5-Minute Setup

#### 1. Get Your Gemini API Key (2 minutes)
🔑 **IMPORTANT - Do this first!**

```
1. Go to: https://aistudio.google.com/app/apikeys
2. Click "Get API key"
3. Click "Create API key in new project"
4. Copy your API key
```

#### 2. Set Up Environment (2 minutes)

**Windows:**
```bash
# Open PowerShell in this folder
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Configure API Key (1 minute)

**Option A: Using .env (Recommended)**
```bash
cp .env.example .env
# Edit .env and paste your API key next to GEMINI_API_KEY=
```

**Option B: Direct in config.py**
```python
# Open config.py and replace this line:
GEMINI_API_KEY = "your_actual_key_here"
```

---

## ▶️ Running the Backend

### Start Server
```bash
python main.py
```

You should see:
```
🚀 Adaptive Learning Platform Backend
📝 Config file: config.py
🔑 GEMINI_API_KEY set: ✅ Yes
💾 Database: adaptive_learning.db
🌐 Starting server on http://127.0.0.1:8000
📚 API Docs: http://127.0.0.1:8000/docs
```

### Test the API

**Interactive Docs:**
Visit: http://127.0.0.1:8000/docs

**Using Python Client:**
```bash
python example_client.py
```

---

## 📡 API Quick Reference

### Create User
```bash
curl -X POST http://127.0.0.1:8000/user/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John",
    "skill_level": "beginner",
    "goal": "mastery",
    "initial_topic": "algebra"
  }'
```

### Get Question
```bash
curl -X POST http://127.0.0.1:8000/get_question \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-user-id",
    "topic": "algebra"
  }'
```

### Submit Answer
```bash
curl -X POST http://127.0.0.1:8000/submit_answer \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-user-id",
    "exercise_id": "exercise-id",
    "user_answer": "4",
    "response_time": 10.5,
    "hints_used": 0
  }'
```

---

## 🧠 How It Works

```
User answers question
         ↓
Backend calculates score using weighted formula
         ↓
Updates mastery level (0-100%)
         ↓
Decision engine analyzes:
  - Accuracy
  - Response time
  - Consistency
         ↓
Recommends next action:
  - Keep same difficulty
  - Increase difficulty (mastery > 85%)
  - Lower difficulty (mastery < 50%)
  - Provide hints/explanations
```

---

## 📊 Scoring Formula

```
Score = (1/n) × Σ(Base × Difficulty × HintPenalty)

Base = 1.0 (correct) or 0.0 (incorrect)
Difficulty = 0.8 (easy), 1.0 (medium), 1.2 (hard)
HintPenalty = 1.0 (no hints), 0.6 (1 hint), 0.2 (2+ hints)

Example: Correct, Hard question, 1 hint
Score = 1.0 × 1.2 × 0.6 = 0.72
```

---

## 🎯 Difficulty Adaptation

| Mastery Score | Action | Difficulty |
|---|---|---|
| > 85% | Advance | Increase |
| 50-85% | Continue | Keep Same |
| < 50% | Review | Decrease |
| Response Time 2x+ | Struggling | Decrease |

---

## 📁 Project Files

| File | Purpose |
|---|---|
| `config.py` | ⚙️ Configuration & API keys |
| `models.py` | 📋 Data models |
| `scoring.py` | 📊 Scoring engine |
| `decision_engine.py` | 🤖 AI brain |
| `gemini_integration.py` | 🔗 Gemini API |
| `database.py` | 💾 SQLite operations |
| `main.py` | 🌐 FastAPI app |
| `example_client.py` | 📱 Client example |
| `test_backend.py` | ✅ Unit tests |

---

## 🧪 Testing

```bash
# Run all tests
pytest test_backend.py -v

# Run specific test
pytest test_backend.py::TestScoringEngine -v
```

---

## 🆘 Troubleshooting

### Issue: "GEMINI_API_KEY not set"
**Solution:** Add your key to .env or config.py

### Issue: Port 8000 in use
**Solution:** 
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

### Issue: Database errors
**Solution:**
```bash
# Delete database and restart (creates new one)
rm adaptive_learning.db
python main.py
```

### Issue: Gemini API errors
Make sure:
- API key is valid
- API key has Generative AI enabled
- You have API billing set up

---

## 🔗 Available Topics

```python
[
    "arithmetic",
    "algebra",
    "geometry",
    "trigonometry",
    "calculus",
    "statistics",
    "logarithms"
]
```

Add more in `config.py` → `TOPICS` list

---

## 💡 Pro Tips for Hackathon

1. **Test without API key** (offline mode):
   - Server works without API key
   - Returns dummy questions for testing
   - Perfect for frontend development

2. **Mock Gemini Responses**:
   - Edit `gemini_integration.py` → `_get_dummy_question()`
   - Add your own test questions

3. **Database Persistence**:
   - All data saved automatically
   - Database persists between restarts
   - Check with: `sqlite3 adaptive_learning.db`

4. **Quick Database Reset**:
   ```bash
   rm adaptive_learning.db
   python main.py  # Creates fresh database
   ```

5. **Enable Logging**:
   - Watch terminal for debug info
   - All API calls logged

---

## 🌐 Frontend Integration

### Example React Hook:
```javascript
const [question, setQuestion] = useState(null);

// Get question
const getQuestion = async (userId) => {
  const response = await fetch('http://127.0.0.1:8000/get_question', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: userId })
  });
  const data = await response.json();
  setQuestion(data);
};

// Submit answer
const submitAnswer = async (userId, exerciseId, answer, timeSeconds) => {
  const response = await fetch('http://127.0.0.1:8000/submit_answer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      exercise_id: exerciseId,
      user_answer: answer,
      response_time: timeSeconds,
      hints_used: 0
    })
  });
  const result = await response.json();
  console.log(result.feedback);
};
```

---

## 📈 Monitoring Performance

```bash
# View database stats
python -c "
import sqlite3
conn = sqlite3.connect('adaptive_learning.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
print('Tables:', cursor.fetchall())
cursor.execute('SELECT COUNT(*) FROM users')
print('Users:', cursor.fetchone()[0])
cursor.execute('SELECT COUNT(*) FROM user_answers')
print('Answers:', cursor.fetchone()[0])
"
```

---

## 🎓 Example Workflow

```python
# 1. Create user
POST /user/create
→ Get user_id

# 2. Get question (automatic difficulty adjustment)
POST /get_question
→ Get exercise_id, question, difficulty

# 3. User solves (your frontend)
# (Timer running, user thinks...)

# 4. Submit answer (with time & hints used)
POST /submit_answer
→ Get is_correct, explanation, mastery_score

# 5. Check next action
POST /next_action
→ Get recommended difficulty, topic, action

# LOOP: Go to step 2 for next question!
```

---

## 📚 Full Documentation

See `README.md` for:
- Complete API reference
- Database schema
- Detailed configuration
- Deployment tips
- Future enhancements

---

## ✅ Checklist Before Hackathon

- [ ] API key obtained from Google AI Studio
- [ ] API key added to .env or config.py
- [ ] `pip install -r requirements.txt` completed
- [ ] `python main.py` starts successfully
- [ ] Can access http://127.0.0.1:8000/docs
- [ ] Example client runs: `python example_client.py`
- [ ] Database created: `adaptive_learning.db` exists
- [ ] All tests pass: `pytest test_backend.py -v`

---

## 🚀 You're Ready!

Your adaptive learning backend is ready to power your hackathon project!

**Next Steps:**
1. Build your frontend
2. Integrate with these endpoints
3. Customize topics/questions
4. Deploy to production
5. Win your hackathon! 🏆

---

## 📞 Need Help?

- **API Docs**: http://127.0.0.1:8000/docs
- **Gemini Docs**: https://ai.google.dev/
- **FastAPI Docs**: https://fastapi.tiangolo.com/

**Happy Hacking! 🎉**
