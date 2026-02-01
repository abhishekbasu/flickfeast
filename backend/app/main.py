import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agents_flow import build_menu
from .auth import GoogleAuthError, verify_google_token
from .movie_api import MovieApiError, search_movies
from .config import settings

app = FastAPI(title="flickfeast")

logger = logging.getLogger(__name__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class GoogleTokenRequest(BaseModel):
    id_token: str


class MovieRequest(BaseModel):
    title: str


class MovieSearchResponse(BaseModel):
    title: str
    year: str | None = None
    imdb_id: str | None = None
    poster: str | None = None


class MenuItemResponse(BaseModel):
    name: str
    reason: str


class RecipeResponse(BaseModel):
    title: str
    source: str
    url: str


class MenuResponse(BaseModel):
    items: list[MenuItemResponse]
    recipes: list[RecipeResponse] = []
    notes: str | None = None


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/google")
async def auth_google(payload: GoogleTokenRequest) -> dict[str, str | None]:
    try:
        user = verify_google_token(payload.id_token)
    except GoogleAuthError as exc:
        logger.exception("Google auth failed")
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return user


@app.post("/movies/lookup")
async def lookup_movie(payload: MovieRequest) -> dict[str, str]:
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Movie title is required")

    return {"message": f"Thanks! You entered '{title}'."}


@app.post("/movies/menu", response_model=MenuResponse)
async def movie_menu(payload: MovieRequest) -> dict[str, list[dict[str, str]] | str]:
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Movie title is required")

    menu = await build_menu(title)
    if not menu.get("items"):
        detail = menu.get("notes", "Menu generation failed")
        logger.warning("No menu items found for title=%s detail=%s", title, detail)
        if "not found" in str(detail).lower():
            raise HTTPException(status_code=404, detail=detail)
        raise HTTPException(status_code=502, detail=detail)

    return menu


@app.get("/movies/search", response_model=list[MovieSearchResponse])
async def movie_search(query: str) -> list[dict[str, str]]:
    query = query.strip()
    if not query:
        return []
    try:
        return search_movies(query)
    except MovieApiError as exc:
        logger.exception("Movie search failed for query=%s", query)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
