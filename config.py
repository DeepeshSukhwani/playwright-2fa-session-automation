
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

AUTH_DIR = BASE_DIR / ".auth"
SESSION_FILE = AUTH_DIR / "github_state.json"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
DOWNLOADS_DIR = BASE_DIR / "downloads"

GITHUB_BASE_URL = "https://github.com"
GITHUB_LOGIN_URL = f"{GITHUB_BASE_URL}/login"

GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "")
GITHUB_PASSWORD = os.getenv("GITHUB_PASSWORD", "")
GITHUB_TOTP_SECRET = os.getenv("GITHUB_TOTP_SECRET", "")


def prepare_directories() -> None:
    """Create directories required by the automation."""
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
