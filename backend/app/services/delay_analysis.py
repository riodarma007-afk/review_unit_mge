from typing import List, Dict, Any
from collections import defaultdict


def _safe_float(val, default=0.0):
    """Safely convert a value to float."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


class DelayAnalysisService:
    @staticmethod
    def calculate_pareto(events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Menghitung pareto delay operasional dan breakdown (all events atau non-mechanical, 
        kita hitung semua event karena status mekanikal juga bagian dari downtime/delay).
        Mengembalikan total_delay_hours dan list items.
        """
        if not events:
            return {"total_delay_hours": 0.0, "items": []}
        
        # Filter event yang durasinya > 0
        valid_events = [e for e in events if _safe_float(e.get('Durasi')) > 0]
        if not valid_events:
            return {"total_delay_hours": 0.0, "items": []}
        
        # Hitung total hours
        total_hours = sum(_safe_float(e.get('Durasi')) for e in valid_events)
        
        # Group by (Status, Code) dan sum Durasi
        grouped = defaultdict(float)
        for event in valid_events:
            status = str(event.get('Status', ''))
            code = event.get('Code', 0)
            key = (status, code)
            grouped[key] += _safe_float(event.get('Durasi'))
        
        # Urutkan menurun berdasarkan Durasi
        sorted_items = sorted(grouped.items(), key=lambda x: x[1], reverse=True)
        
        items = []
        cumulative_percent = 0.0
        
        for (status, code), hours in sorted_items:
            percent = (hours / total_hours) * 100.0 if total_hours > 0 else 0.0
            cumulative_percent += percent
            
            items.append({
                "status": status,
                "code": int(code) if code is not None else 0,
                "hours": round(hours, 2),
                "percent": round(percent, 2),
                "cumulative_percent": round(cumulative_percent, 2)
            })
            
        return {
            "total_delay_hours": round(total_hours, 2),
            "items": items
        }
