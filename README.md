# flickfeast

## What it does
FlickFeast brings iconic movie moments to your table. Whether you're recreating the ratatouille from Ratatouille, the butter beer from Harry Potter, or the big kahuna burger from Pulp Fiction, FlickFeast transforms movie nights into immersive culinary experiences. Look up your favorite film, and FlickFeast delivers authentic recipes for the most memorable dishes from that movie—complete with step-by-step instructions to nail every detail. Perfect for themed watch parties, film club gatherings, or impressing fellow cinephiles with your attention to detail.

## How to run

### Backend (FastAPI)

1. Set env vars:
   - `GOOGLE_CLIENT_ID` (from Google Cloud Console)
   - `GOOGLE_CLIENT_SECRET` (from Google Cloud Console)
   - `GOOGLE_REDIRECT_URI` (set to `http://localhost:5173/auth/google/callback` for local; served from `frontend/public/auth/google/callback/index.html`)
   - `ALLOWED_ORIGINS` (comma-separated, default `http://localhost:5173`)
   - `OPENAI_API_KEY` (required for Agents SDK)
   - `OPENAI_MODEL` (optional, defaults to `gpt-4o-mini`)
   - `OPENAI_IMAGE_MODEL` (optional, defaults to `gpt-image-1-mini`)
   - `OMDB_API_KEY` or `TMDB_API_KEY` / `TMDB_API_READ_ACCESS_TOKEN` (movie lookup)
   - `SPOONACULAR_API_KEY` (optional recipe search; falls back to TheMealDB)

2. Install deps (example with pip):
   - `python -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt` (if you export from `pyproject.toml`) or install via your preferred tool.

3. Run:
   - `uvicorn backend.app.main:app --reload`

### Frontend (Vue + Vite)

1. Set env vars:
   - `VITE_GOOGLE_CLIENT_ID`
   - `VITE_API_BASE_URL` (default `http://localhost:8000`)

2. Install deps:
   - `cd frontend && npm install`

3. Run:
   - `npm run dev`

### Notes
- The UI shows a Google sign-in button first. After login, it prompts for a movie title.
- The backend verifies the Google ID token using `GOOGLE_CLIENT_ID`.
- In Google Cloud Console, set the OAuth client type to Web, add `http://localhost:5173` to Authorized JavaScript origins, and reuse the same client ID for both frontend and backend.
- Movie lookup uses OMDb when `OMDB_API_KEY` is set, otherwise it falls back to TMDB. TMDB prefers `TMDB_API_READ_ACCESS_TOKEN` (v4) and falls back to `TMDB_API_KEY` (v3 or v4).
- Agents flow uses `PartyPlanner` as the manager agent. `MovieSearcher` verifies the movie and returns details, `MovieFoodItems` builds the menu, `RecipeAgent` optionally generates one recipe per item, and `FoodPhotoGenerator` creates images for each menu item.

## Demo Steps
Open the site to see the splash. Click "Continue with Google" and complete login. After redirect, click "Start
planning." Search for a movie title, choose one from the results, and wait for "Generating your dream menu." The menu appears
with food items and images. Click any food item to open a modal with the generated recipe, ingredients, and steps. Use "Search
another movie" to restart.