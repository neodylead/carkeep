import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-only-change-this-key"
    )

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'carlog.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
