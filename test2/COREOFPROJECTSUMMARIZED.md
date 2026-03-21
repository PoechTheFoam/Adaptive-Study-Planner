# Axis Mentor

Axis Mentor is a purely web-based adaptive AI math partner. It registers a learner, generates a quiz with Gemini when available, scores each response with the weighted formula you specified, tracks mastery over time, and saves a learner profile in SQLite for future sessions.

## What it does

- Register a learner by topic and education level.
- Generate adaptive multiple-choice math questions in the browser.
- Score each question using `Base x Difficulty x HintPenalty`.
- Flag struggling behavior when response time spikes beyond the learner's average.
- Detect inconsistent answer patterns and surface a suspicion level.
- Save every session and update the next difficulty recommendation.
- Show explanations for each question and an overall evaluation after submission.

## Stack

- Backend: pure Python WSGI app
- Frontend: static HTML, CSS, and vanilla JavaScript
- Storage: SQLite
- AI: Gemini REST API with a local math-question fallback( in case GEMINI fails!!!)

## Run it

```bash
python run.py
```

Then open `http://127.0.0.1:8765`.
#important:
so appearently if the app is access via pasting the address straight to the browser theres might be bug going on.
-> So its best to run it through the instruction above

## Gemini setup

- The app reads configuration from `.env`.
-
`
