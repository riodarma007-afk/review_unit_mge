import pymysql
import sys
import os

# Add parent directory to path so we can import from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from app.core.database import get_db_connection

def create_table():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            DROP TABLE IF EXISTS Optrack_target_settings;
            CREATE TABLE Optrack_target_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                activity VARCHAR(50),
                pit VARCHAR(50),
                year INT,
                month INT,
                pa_target FLOAT,
                ua_target FLOAT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
            cursor.execute("DROP TABLE IF EXISTS Optrack_target_settings;")
            cursor.execute("""
            CREATE TABLE Optrack_target_settings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                activity VARCHAR(50),
                pit VARCHAR(50),
                year INT,
                month INT,
                pa_target FLOAT,
                ua_target FLOAT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)
        conn.commit()
        print("Table Optrack_target_settings created successfully.")
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_table()
