# flickfeast

Minimal full-stack starter for a Google-authenticated movie prompt flow.

## Backend (FastAPI)

1. Set env vars:
   - `GOOGLE_CLIENT_ID` (from Google Cloud Console)
   - `ALLOWED_ORIGINS` (comma-separated, default `http://localhost:5173`)

2. Install deps (example with pip):
   - `python -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt` (if you export from `pyproject.toml`) or install via your preferred tool.

3. Run:
   - `uvicorn backend.app.main:app --reload`

## Frontend (Vue + Vite)

1. Set env vars:
   - `VITE_GOOGLE_CLIENT_ID`
   - `VITE_API_BASE_URL` (default `http://localhost:8000`)

2. Install deps:
   - `cd frontend && npm install`

3. Run:
   - `npm run dev`

## Notes
- The UI shows a Google sign-in button first. After login, it prompts for a movie title.
- The backend verifies the Google ID token using `GOOGLE_CLIENT_ID`.
