from typing import Optional, List, Dict, Any
from datetime import date
from app.core.database import get_db_connection

class OptrackRepository:
    def __init__(self):
        pass

    def _build_where_clause(self, table_prefix="", **filters):
        p = f"{table_prefix}." if table_prefix else ""
        conditions = [f"({p}is_deleted = 0 OR {p}is_deleted IS NULL)"]
        params = {}
        
        if filters.get('date_from'):
            conditions.append(f"{p}Date >= %(date_from)s")
            params['date_from'] = filters['date_from']
        if filters.get('date_to'):
            conditions.append(f"{p}Date <= %(date_to)s")
            params['date_to'] = filters['date_to']
        if filters.get('shift'):
            conditions.append(f"{p}Shift = %(shift)s")
            params['shift'] = filters['shift']
        if filters.get('pit'):
            conditions.append(f"{p}PIT = %(pit)s")
            params['pit'] = filters['pit']
        if filters.get('unit_code'):
            conditions.append(f"{p}Unit_Code = %(unit_code)s")
            params['unit_code'] = filters['unit_code']
        if filters.get('activity'):
            conditions.append(f"{p}Activity = %(activity)s")
            params['activity'] = filters['activity']
            
        where_clause = " AND ".join(conditions)
        return where_clause, params

    def get_data_utama(self, **filters) -> List[Dict[str, Any]]:
        """Returns list of dicts instead of DataFrame"""
        where_clause, params = self._build_where_clause(**filters)
        query = f"""
            SELECT 
                ID_data, Date, Shift, PIT, Unit_Code, Activity, 
                MOHH, WH, Downtime, Delay, Idle, Ritasi 
            FROM optrack_data_event 
            WHERE {where_clause}
        """
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()
            conn.close()
            return list(result) if result else []
        except Exception as e:
            print(f"Database error in get_data_utama: {e}")
            return []

    def get_events(self, **filters) -> List[Dict[str, Any]]:
        """Returns list of dicts instead of DataFrame"""
        where_clause, params = self._build_where_clause(table_prefix="d", **filters)
        
        query = f"""
            SELECT 
                e.ID_data_input AS ID_data_Input, 
                CAST(e.Event AS SIGNED) AS Code, 
                COALESCE(ev.Event, e.Event) AS Status, 
                COALESCE(ev.Category, '') AS Category,
                e.Duration AS Durasi, 
                '' AS Time, 
                e.Jam_start AS Start, 
                e.Jam_stop AS Stop 
            FROM optrack_breakdown_list e
            INNER JOIN optrack_data_event d ON e.ID_data_input = d.ID_data
            LEFT JOIN optrack_database_event ev ON e.Event = ev.ID_Event
            WHERE {where_clause}
              AND (e.is_deleted = 0 OR e.is_deleted IS NULL)
        """
        
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()
            conn.close()
            return list(result) if result else []
        except Exception as e:
            print(f"Database error in get_events: {e}")
            return []

    def get_filter_options(self):
        try:
            conn = get_db_connection()
            query = "SELECT DISTINCT Unit_Code, PIT, Shift, Activity, Date FROM optrack_data_event WHERE (is_deleted = 0 OR is_deleted IS NULL)"
            with conn.cursor() as cursor:
                cursor.execute(query)
                result = cursor.fetchall()
            conn.close()
            
            if not result:
                return {
                    "units": [], "pits": [], "shifts": [], "activities": [], 
                    "date_range": {"min": "", "max": ""}
                }
            
            units = set()
            pits = set()
            shifts = set()
            activities = set()
            dates = []
            
            for row in result:
                if row.get('Unit_Code') is not None:
                    units.add(row['Unit_Code'])
                if row.get('PIT') is not None:
                    pits.add(row['PIT'])
                if row.get('Shift') is not None:
                    shifts.add(row['Shift'])
                if row.get('Activity') is not None:
                    activities.add(row['Activity'])
                if row.get('Date') is not None:
                    dates.append(row['Date'])
            
            min_date = min(dates) if dates else ""
            max_date = max(dates) if dates else ""
            
            return {
                "units": sorted(list(units)),
                "pits": sorted(list(pits)),
                "shifts": sorted(list(shifts)),
                "activities": sorted(list(activities)),
                "date_range": {
                    "min": str(min_date) if min_date else "",
                    "max": str(max_date) if max_date else ""
                }
            }
        except Exception as e:
            print(f"Database error in get_filter_options: {e}")
            return {
                "units": [], "pits": [], "shifts": [], "activities": [], 
                "date_range": {"min": "", "max": ""}
            }

    # --- Backward-compatible aliases (old names) ---
    def get_data_utama_df(self, **filters):
        """Alias for backward compatibility - returns list of dicts"""
        return self.get_data_utama(**filters)
    
    def get_events_df(self, **filters):
        """Alias for backward compatibility - returns list of dicts"""
        return self.get_events(**filters)
