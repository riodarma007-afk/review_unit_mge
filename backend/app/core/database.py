import pymysql
from app.core.config import settings

def get_db_connection():
    return pymysql.connect(
        host=settings.DB_HOST,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        database=settings.DB_NAME,
        port=int(settings.DB_PORT),
        cursorclass=pymysql.cursors.DictCursor
    )
