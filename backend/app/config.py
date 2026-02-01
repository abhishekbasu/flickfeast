import logging
import os
from pathlib import Path

from dotenv import load_dotenv


_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_ENV_PATH)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(_ENV_PATH.parent / "server.log"),
        logging.StreamHandler(),
    ],
)


class Settings:
    def __init__(self) -> None:
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        self.allowed_origins = [
            origin.strip()
            for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(
                ","
            )
            if origin.strip()
        ]
        self.omdb_api_key = os.getenv("OMDB_API_KEY", "")
        self.tmdb_api_key = os.getenv("TMDB_API_KEY", "")
        self.tmdb_read_access_token = os.getenv("TMDB_API_READ_ACCESS_TOKEN", "")
        self.spoonacular_api_key = os.getenv("SPOONACULAR_API_KEY", "")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.openai_image_model = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1")


settings = Settings()
