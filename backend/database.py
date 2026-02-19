import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import time

load_dotenv()

def get_db_connection(retries=3):
    for attempt in range(retries):
        try:
            return psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'cloudproof'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'postgres'),
                connect_timeout=10
            )
        except psycopg2.OperationalError as e:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            raise Exception(f"Database connection failed after {retries} attempts: {str(e)}")

def execute_query(query, params=None, fetch=False):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, params)
        result = cursor.fetchall() if fetch else None
        conn.commit()
        return result
    except Exception as e:
        if conn:
            conn.rollback()
        raise Exception(f"Query execution failed: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
