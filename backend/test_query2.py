from app.core.database import get_db_connection
conn=get_db_connection()
c=conn.cursor()
c.execute("SELECT Unit_Code, sum(MOHH), sum(Downtime), sum(WH) FROM optrack_summary_mohh WHERE Date = '2026-06-28' AND Unit_Code IN ('GHT 721', 'GHT 749', 'GHT 750') GROUP BY Unit_Code")
for r in c.fetchall():
    print(r)
