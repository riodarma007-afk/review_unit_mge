import sqlalchemy
from sqlalchemy import create_engine, inspect

DB_HOST="103.58.102.44"
DB_PORT="3306"
DB_USER="mge_planning"
DB_PASSWORD="PlanningMGE2026"
DB_NAME="mge_planning_staging"

url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(url)

try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print("Tables found:", tables)
    
    target_tables = ['Optrack_data_event', 'Optrack_breakdown_list', 'optrack_summary_mohh']
    
    for t in target_tables:
        if t in tables:
            print(f"\n--- Schema for {t} ---")
            columns = inspector.get_columns(t)
            for col in columns:
                print(f"{col['name']}: {col['type']}")
        else:
            print(f"\nTable {t} NOT FOUND! Available tables: {tables}")
except Exception as e:
    print("Error connecting or inspecting:", e)
