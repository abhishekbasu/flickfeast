# flickfeast

Minimal full-stack starter for a Google-authenticated movie prompt flow.

## Backend (FastAPI)

1. Set env vars:
   - `GOOGLE_CLIENT_ID` (from Google Cloud Console)
   - `ALLOWED_ORIGINS` (comma-separated, default `http://localhost:5173`)
   - `OPENAI_API_KEY` (required for Agents SDK)
   - `OPENAI_MODEL` (optional, defaults to `gpt-4o-mini`)
   - `OMDB_API_KEY` or `TMDB_API_KEY` / `TMDB_API_READ_ACCESS_TOKEN` (movie lookup)

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
- In Google Cloud Console, set the OAuth client type to Web, add `http://localhost:5173` to Authorized JavaScript origins, and reuse the same client ID for both frontend and backend.
- Movie lookup uses OMDb when `OMDB_API_KEY` is set, otherwise it falls back to TMDB. TMDB prefers `TMDB_API_READ_ACCESS_TOKEN` (v4) and falls back to `TMDB_API_KEY` (v3 or v4).
