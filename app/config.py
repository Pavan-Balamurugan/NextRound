import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "demo")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "demo")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./hackfest.db")

    @property
    def demo_mode(self) -> bool:
        key = (self.GROQ_API_KEY or "").strip().lower()
        return key in ("", "demo")


settings = Settings()
