from app.core.database import get_db_connection
conn=get_db_connection()
c=conn.cursor()
c.execute("SELECT Unit_Code, MOHH, Downtime, WH FROM optrack_summary_mohh WHERE Unit_Code IN ('GHT 701', 'GHT 721', 'GHT 750', 'GHT 749', 'GHT 744') LIMIT 10")
for r in c.fetchall():
    print(r)
