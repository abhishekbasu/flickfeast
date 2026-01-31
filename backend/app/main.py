from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .auth import GoogleAuthError, verify_google_token
from .config import settings

app = FastAPI(title="flickfeast")

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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/google")
async def auth_google(payload: GoogleTokenRequest) -> dict[str, str | None]:
    try:
        user = verify_google_token(payload.id_token)
    except GoogleAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return user


@app.post("/movies/lookup")
async def lookup_movie(payload: MovieRequest) -> dict[str, str]:
    title = payload.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Movie title is required")

    return {"message": f"Thanks! You entered '{title}'."}
