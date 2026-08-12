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
    def calculate_pareto(events: List[Dict[str, Any]], plan_data: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Menghitung pareto delay operasional dan breakdown (all events atau non-mechanical, 
        kita hitung semua event karena status mekanikal juga bagian dari downtime/delay).
        Mengembalikan total_delay_hours dan list items.
        """
        if plan_data is None:
            plan_data = {}
            
        if not events:
            return {"total_delay_hours": 0.0, "total_idle": 0.0, "total_delay": 0.0, "total_downtime": 0.0, "items": []}
        
        # Filter event yang durasinya > 0
        valid_events = [e for e in events if _safe_float(e.get('Durasi')) > 0]
        if not valid_events:
            return {"total_delay_hours": 0.0, "total_idle": 0.0, "total_delay": 0.0, "total_downtime": 0.0, "items": []}
        
        # Hitung total hours
        total_hours = sum(_safe_float(e.get('Durasi')) for e in valid_events)
        
        # Category totals
        total_idle = 0.0
        total_delay = 0.0
        total_downtime = 0.0
        
        # Group by (Status, Code) dan sum Durasi, track category
        grouped = defaultdict(lambda: {'hours': 0.0, 'category': None})
        for event in valid_events:
            status = str(event.get('Status', ''))
            code = event.get('Code', 0)
            category = str(event.get('Category', '')).strip().lower()
            key = (status, code)
            grouped[key]['hours'] += _safe_float(event.get('Durasi'))
            if grouped[key]['category'] is None and category:
                grouped[key]['category'] = category
            
            # Sum category totals
            durasi = _safe_float(event.get('Durasi'))
            if category == 'idle':
                total_idle += durasi
            elif category == 'delay':
                total_delay += durasi
            elif category == 'downtime':
                total_downtime += durasi
        
        # Urutkan menurun berdasarkan Durasi
        sorted_items = sorted(grouped.items(), key=lambda x: x[1]['hours'], reverse=True)
        
        items = []
        cumulative_percent = 0.0
        
        for (status, code), data in sorted_items:
            hours = data['hours']
            category = data['category'] or 'delay'
            percent = (hours / total_hours) * 100.0 if total_hours > 0 else 0.0
            cumulative_percent += percent
            
            # Fetch plan_hours from aggregated plan_data dict (case insensitive match)
            matched_plan_hours = 0.0
            for p_name, p_hours in plan_data.items():
                if p_name.lower() == status.lower():
                    matched_plan_hours = p_hours
                    break
            
            items.append({
                "status": status,
                "code": int(code) if code is not None else 0,
                "hours": round(hours, 2),
                "plan_hours": round(matched_plan_hours, 2),
                "percent": round(percent, 2),
                "cumulative_percent": round(cumulative_percent, 2),
                "category": category
            })
            
        return {
            "total_delay_hours": round(total_hours, 2),
            "total_idle": round(total_idle, 2),
            "total_delay": round(total_delay, 2),
            "total_downtime": round(total_downtime, 2),
            "items": items
        }
