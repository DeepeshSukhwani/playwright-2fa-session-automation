import logging
from pathlib import Path

from config import ARTIFACTS_DIR, prepare_directories


def configure_logging() -> logging.Logger:
    """Log automation progress to the console and a file."""
    prepare_directories()

    log_file = Path(ARTIFACTS_DIR) / "automation.log"

    # Keep logs consistent across all modules.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
        force=True,
    )

    return logging.getLogger("github_automation")