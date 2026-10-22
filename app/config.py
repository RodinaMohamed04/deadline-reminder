"""Settings, read from environment variables (and an optional .env file)."""
import os
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-only-secret-change-me-dev-only-secret")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./deadlines.db")
    ACCESS_TOKEN_MINUTES: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
    SCAN_INTERVAL_MINUTES: int = int(os.getenv("SCAN_INTERVAL_MINUTES", "15"))
    REMINDER_WINDOWS_HOURS: list[int] = sorted(
        int(h) for h in os.getenv("REMINDER_WINDOWS_HOURS", "72,24,3").split(",") if h.strip()
    )
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "reminders@example.com")
    ENABLE_SCHEDULER: bool = os.getenv("ENABLE_SCHEDULER", "1") == "1"


settings = Settings()
