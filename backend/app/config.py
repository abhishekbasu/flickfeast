import os


class Settings:
    def __init__(self) -> None:
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
        self.allowed_origins = [
            origin.strip()
            for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
            if origin.strip()
        ]


settings = Settings()
