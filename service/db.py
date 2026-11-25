import os
import psycopg
from dotenv import load_dotenv
import logging
load_dotenv()

logger = logging.getLogger(__name__)

def get_connection():
    conn = psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        sslmode="require",
        connect_timeout=10,
    )
    logger.info("DB Connected")
    return conn

def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()