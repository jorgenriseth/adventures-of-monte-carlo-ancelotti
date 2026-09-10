import os

from dotenv import load_dotenv

DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:password@localhost:5432/fpl"

load_dotenv()


def get_database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
