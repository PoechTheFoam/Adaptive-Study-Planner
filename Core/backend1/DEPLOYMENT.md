# Deployment Guide

## Recommended Path

Deploy the backend and frontend together as one FastAPI web service.
The app already serves the browser UI at `/`, so you only need one deployment.

Recommended host: Render

Why this path:
- One service instead of separate frontend and backend hosting
- Simple FastAPI start command
- Good monorepo support with `rootDir`
- Built-in health checks and easy custom domain setup

## Before You Deploy

1. Push the latest code to GitHub.
2. Keep your real Gemini key out of git.
3. Keep using `Core/backend1/.env.example` only as a template.

## Render Setup

This repo now includes a root `render.yaml` blueprint.

It configures:
- `Core/backend1` as the service root
- `pip install -r requirements.txt` as the build command
- `uvicorn main:app --host 0.0.0.0 --port $PORT` as the start command
- `/health` as the health check
- Python `3.11.11`

### Deploy Steps

1. Push this repository to GitHub.
2. In Render, create a new Blueprint or Web Service from the repo.
3. If you use the Blueprint flow, Render will read `render.yaml`.
4. Add `GEMINI_API_KEY` in the Render dashboard.
5. Deploy and open the generated `onrender.com` URL.

## Data Persistence

The app currently uses SQLite.

Important:
- Render uses an ephemeral filesystem by default.
- Without persistent storage, SQLite data can reset on redeploy or restart.

### Fast Demo Option

Do nothing extra.

Result:
- The app works online
- Learner data is temporary

### Better Persistent Option

Attach a persistent disk in Render and set:

```env
DATABASE_PATH=/var/data/adaptive_learning.db
```

Suggested disk mount path:

```text
/var/data
```

## Local Production-Style Run

From `Core/backend1`:

```powershell
$env:HOST="127.0.0.1"
$env:PORT="8000"
$env:UVICORN_RELOAD="false"
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Then open:

```text
http://127.0.0.1:8000/
```

## Later Upgrade Path

If you want a more durable production setup later:
- keep Render for hosting
- replace SQLite with Postgres
- keep secrets only in the Render dashboard
- add a custom domain

The current setup is enough for a clean first web deployment.
