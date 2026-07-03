import pandas as pd
from typing import List, Dict, Any

class DelayAnalysisService:
    @staticmethod
    def calculate_pareto(df_events: pd.DataFrame) -> Dict[str, Any]:
        """
        Menghitung pareto delay operasional dan breakdown (all events atau non-mechanical, 
        kita hitung semua event karena status mekanikal juga bagian dari downtime/delay).
        Mengembalikan total_delay_hours dan list items.
        """
        if df_events.empty or 'Durasi' not in df_events or 'Status' not in df_events:
            return {"total_delay_hours": 0.0, "items": []}
            
        # Filter event yang durasinya > 0
        df_valid = df_events[df_events['Durasi'] > 0].copy()
        if df_valid.empty:
            return {"total_delay_hours": 0.0, "items": []}
            
        total_hours = df_valid['Durasi'].sum()
        
        # Group by Status dan Code
        df_grouped = df_valid.groupby(['Status', 'Code'], as_index=False)['Durasi'].sum()
        
        # Urutkan menurun berdasarkan Durasi
        df_sorted = df_grouped.sort_values(by='Durasi', ascending=False).reset_index(drop=True)
        
        items = []
        cumulative_percent = 0.0
        
        for _, row in df_sorted.iterrows():
            hours = row['Durasi']
            percent = (hours / total_hours) * 100.0 if total_hours > 0 else 0.0
            cumulative_percent += percent
            
            items.append({
                "status": row['Status'],
                "code": int(row['Code']),
                "hours": round(hours, 2),
                "percent": round(percent, 2),
                "cumulative_percent": round(cumulative_percent, 2)
            })
            
        return {
            "total_delay_hours": round(total_hours, 2),
            "items": items
        }
