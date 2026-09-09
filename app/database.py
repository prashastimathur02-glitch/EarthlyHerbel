import os
import psycopg
from dotenv import load_dotenv


load_dotenv()


def get_db_connection():
    return psycopg.connect(
        host=os.getenv("DATABASE_HOST", "localhost"),
        port=os.getenv("DATABASE_PORT", "5432"),
        dbname=os.getenv("DATABASE_NAME", "earthlyherbel"),
        user=os.getenv("DATABASE_USER", "postgres"),
        password=os.getenv("DATABASE_PASSWORD"),
    )