from typing import Dict, Any, List
from collections import defaultdict

from app.core.kpi_targets import KPI_TARGETS, MECHANICAL_CODES


def _safe_float(val, default=0.0):
    """Safely convert a value to float."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _safe_int(val, default=0):
    """Safely convert a value to int."""
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


class KpiCalculator:
    @staticmethod
    def calculate_kpi_from_aggs(
        sum_mohh: float, 
        sum_downtime: float, 
        sum_mech_downtime: float, 
        sum_wh: float, 
        sum_ritasi: float
    ) -> Dict[str, Any]:
        """
        Hitung rasio KPI berdasarkan hasil agregasi mentah.
        Penting: Hindari division by zero.
        """
        pa = None
        if sum_mohh > 0:
            pa = ((sum_mohh - sum_downtime) / sum_mohh) * 100.0
            
        ma = None
        if sum_mohh > 0:
            ma = ((sum_mohh - sum_mech_downtime) / sum_mohh) * 100.0
            
        ua = None
        avail_hours = sum_mohh - sum_downtime
        if avail_hours > 0:
            ua = (sum_wh / avail_hours) * 100.0
            
        eu = None
        if sum_mohh > 0:
            eu = (sum_wh / sum_mohh) * 100.0
            
        productivity = None
        if sum_wh > 0:
            productivity = sum_ritasi / sum_wh
            
        return {
            "ma_percent": round(ma, 2) if ma is not None else None,
            "pa_percent": round(pa, 2) if pa is not None else None,
            "ua_percent": round(ua, 2) if ua is not None else None,
            "eu_percent": round(eu, 2) if eu is not None else None,
            "total_ritasi": int(sum_ritasi),
            "productivity_rit_per_hour": round(productivity, 2) if productivity is not None else None
        }

    @staticmethod
    def summarize_kpi(data_utama: List[Dict], events: List[Dict]) -> Dict[str, Any]:
        """Hitung KPI level grup (summary total)"""
        if not data_utama:
            return KpiCalculator.calculate_kpi_from_aggs(0, 0, 0, 0, 0)
            
        sum_mohh = sum(_safe_float(row.get('MOHH')) for row in data_utama)
        sum_downtime = sum(_safe_float(row.get('Downtime')) for row in data_utama)
        sum_wh = sum(_safe_float(row.get('WH')) for row in data_utama)
        sum_ritasi = sum(_safe_float(row.get('Ritasi')) for row in data_utama)
        
        sum_mech_downtime = 0
        if events:
            for event in events:
                status = str(event.get('Status', ''))
                durasi = _safe_float(event.get('Durasi'))
                if status in MECHANICAL_CODES:
                    sum_mech_downtime += durasi
            
        return KpiCalculator.calculate_kpi_from_aggs(
            sum_mohh, sum_downtime, sum_mech_downtime, sum_wh, sum_ritasi
        )

    @staticmethod
    def calculate_trend(data_utama: List[Dict], events: List[Dict], group_by: str) -> List[Dict]:
        """
        Hitung trend KPI dengan group_by (Date, Shift, atau PIT).
        Returns list of dicts instead of DataFrame.
        """
        if not data_utama:
            return []
            
        if group_by not in ['Date', 'Shift', 'PIT']:
            group_by = 'Date'  # default
            
        # Agregasi data utama per group
        grouped = defaultdict(lambda: {'MOHH': 0, 'Downtime': 0, 'WH': 0, 'Ritasi': 0})
        for row in data_utama:
            key = str(row.get(group_by, ''))
            grouped[key]['MOHH'] += _safe_float(row.get('MOHH'))
            grouped[key]['Downtime'] += _safe_float(row.get('Downtime'))
            grouped[key]['WH'] += _safe_float(row.get('WH'))
            grouped[key]['Ritasi'] += _safe_float(row.get('Ritasi'))
        
        # Buat lookup: ID_data -> group_by value
        id_to_group = {}
        for row in data_utama:
            id_data = row.get('ID_data')
            if id_data is not None:
                id_to_group[id_data] = str(row.get(group_by, ''))
        
        # Agregasi mech downtime dari event
        mech_downtime_map = defaultdict(float)
        if events:
            for event in events:
                status = str(event.get('Status', ''))
                if status in MECHANICAL_CODES:
                    durasi = _safe_float(event.get('Durasi'))
                    id_input = event.get('ID_data_Input')
                    group_key = id_to_group.get(id_input)
                    if group_key is not None:
                        mech_downtime_map[group_key] += durasi
        
        results = []
        for key, agg in grouped.items():
            mech_dt = mech_downtime_map.get(key, 0)
            kpi = KpiCalculator.calculate_kpi_from_aggs(
                agg['MOHH'], agg['Downtime'], mech_dt, agg['WH'], agg['Ritasi']
            )
            kpi['label'] = key
            results.append(kpi)
            
        return results

    @staticmethod
    def calculate_unit_ranking(data_utama: List[Dict], events: List[Dict], metric: str = 'productivity') -> List[Dict]:
        """Hitung ranking unit berdasarkan metrik tertentu. Returns list of dicts."""
        if not data_utama:
            return []
            
        # Group by Unit_Code
        grouped = defaultdict(lambda: {'MOHH': 0, 'Downtime': 0, 'WH': 0, 'Ritasi': 0})
        for row in data_utama:
            unit = row.get('Unit_Code', '')
            grouped[unit]['MOHH'] += _safe_float(row.get('MOHH'))
            grouped[unit]['Downtime'] += _safe_float(row.get('Downtime'))
            grouped[unit]['WH'] += _safe_float(row.get('WH'))
            grouped[unit]['Ritasi'] += _safe_float(row.get('Ritasi'))
        
        # Buat lookup: ID_data -> Unit_Code
        id_to_unit = {}
        for row in data_utama:
            id_data = row.get('ID_data')
            if id_data is not None:
                id_to_unit[id_data] = row.get('Unit_Code', '')
        
        # Mech downtime per unit
        mech_downtime_map = defaultdict(float)
        if events:
            for event in events:
                status = str(event.get('Status', ''))
                if status in MECHANICAL_CODES:
                    durasi = _safe_float(event.get('Durasi'))
                    id_input = event.get('ID_data_Input')
                    unit = id_to_unit.get(id_input)
                    if unit is not None:
                        mech_downtime_map[unit] += durasi
                
        results = []
        for unit, agg in grouped.items():
            mech_dt = mech_downtime_map.get(unit, 0)
            kpi = KpiCalculator.calculate_kpi_from_aggs(
                agg['MOHH'], agg['Downtime'], mech_dt, agg['WH'], agg['Ritasi']
            )
            
            value = None
            if metric == 'productivity':
                value = kpi['productivity_rit_per_hour']
            elif metric == 'ritasi':
                value = kpi['total_ritasi']
            elif metric == 'ma_percent':
                value = kpi['ma_percent']
            elif metric == 'pa_percent':
                value = kpi['pa_percent']
            elif metric == 'ua_percent':
                value = kpi['ua_percent']
            elif metric == 'eu_percent':
                value = kpi['eu_percent']
                
            if value is not None:
                results.append({'unit_code': unit, 'value': value})
            
        return results

    @staticmethod
    def calculate_all_units_kpi(data_utama: List[Dict], events: List[Dict]) -> list:
        """Hitung KPI lengkap untuk semua unit, mengembalikan list of dict"""
        if not data_utama:
            return []
        
        # Group data utama by Unit_Code
        grouped = defaultdict(lambda: {
            'MOHH': 0, 'Downtime': 0, 'WH': 0, 'Ritasi': 0,
            'Delay': 0, 'Idle': 0, 'dates': set()
        })
        for row in data_utama:
            unit = row.get('Unit_Code', '')
            grouped[unit]['MOHH'] += _safe_float(row.get('MOHH'))
            grouped[unit]['Downtime'] += _safe_float(row.get('Downtime'))
            grouped[unit]['WH'] += _safe_float(row.get('WH'))
            grouped[unit]['Ritasi'] += _safe_float(row.get('Ritasi'))
            grouped[unit]['Delay'] += _safe_float(row.get('Delay'))
            grouped[unit]['Idle'] += _safe_float(row.get('Idle'))
            date_val = row.get('Date')
            if date_val is not None:
                grouped[unit]['dates'].add(str(date_val))
        
        # Buat lookup: ID_data -> Unit_Code
        id_to_unit = {}
        for row in data_utama:
            id_data = row.get('ID_data')
            if id_data is not None:
                id_to_unit[id_data] = row.get('Unit_Code', '')
        
        # Activity breakdown per unit
        activity_agg = defaultdict(lambda: defaultdict(lambda: {'ritasi': 0, 'shifts': 0}))
        for row in data_utama:
            unit = row.get('Unit_Code', '')
            activity = str(row.get('Activity', '')) if row.get('Activity') is not None else 'Unknown'
            activity_agg[unit][activity]['ritasi'] += _safe_float(row.get('Ritasi'))
            activity_agg[unit][activity]['shifts'] += 1
        
        activity_map = {}
        for unit, activities in activity_agg.items():
            act_list = []
            for act_name, act_data in activities.items():
                act_list.append({
                    "activity": act_name,
                    "ritasi": int(act_data['ritasi']),
                    "shifts": act_data['shifts']
                })
            activity_map[unit] = act_list
        
        # Process events
        mech_downtime_map = defaultdict(float)
        breakdown_count_map = defaultdict(int)
        events_pareto_map = defaultdict(lambda: defaultdict(float))
        category_idle_map = {}
        category_delay_map = {}
        category_downtime_map = {}
        
        if events:
            # Merge events with data_utama via id_to_unit lookup
            for event in events:
                id_input = event.get('ID_data_Input')
                unit = id_to_unit.get(id_input)
                if unit is None:
                    continue
                    
                durasi = _safe_float(event.get('Durasi'))
                status = str(event.get('Status', ''))
                category = str(event.get('Category', '')).strip().lower()
                
                # Aggregate categories for Idle, Delay, Downtime
                if category == 'downtime':
                    category_downtime_map[unit] = category_downtime_map.get(unit, 0) + durasi
                elif category == 'delay':
                    category_delay_map[unit] = category_delay_map.get(unit, 0) + durasi
                elif category == 'idle':
                    category_idle_map[unit] = category_idle_map.get(unit, 0) + durasi
                
                # Events pareto (exclude irrelevant statuses)
                if durasi > 0:
                    status_clean = status.strip().lower()
                    exclude_statuses = ['other', 'others', 'no timesheet', 'holiday']
                    if status_clean not in exclude_statuses:
                        events_pareto_map[unit][status] += durasi
                
                # Mech downtime
                if status in MECHANICAL_CODES:
                    mech_downtime_map[unit] += durasi
                    breakdown_count_map[unit] += 1
        
        results = []
        for unit, agg in grouped.items():
            mech_dt = mech_downtime_map.get(unit, 0)
            # Override downtime with actual event sum if exists, else fallback to raw data
            real_downtime = category_downtime_map.get(unit, agg['Downtime'])
            real_delay = category_delay_map.get(unit, agg['Delay'])
            real_idle = category_idle_map.get(unit, agg['Idle'])
            
            kpi = KpiCalculator.calculate_kpi_from_aggs(
                agg['MOHH'], real_downtime, mech_dt, agg['WH'], agg['Ritasi']
            )
            kpi['unit_code'] = unit
            kpi['mohh'] = round(agg['MOHH'], 2)
            kpi['wh'] = round(agg['WH'], 2)
            kpi['downtime'] = round(real_downtime, 2)
            kpi['delay'] = round(real_delay, 2)
            kpi['idle'] = round(real_idle, 2)
            kpi['mech_downtime'] = round(mech_dt, 2)
            kpi['breakdown_count'] = int(breakdown_count_map.get(unit, 0))
            
            days_count = len(agg['dates']) if agg['dates'] else 1
            total_rit = agg['Ritasi']
            kpi['avg_ritasi_per_day'] = round(total_rit / days_count, 1) if days_count > 0 else 0
            
            kpi['activities'] = activity_map.get(unit, [])
            
            # Build events pareto for this unit
            unit_events_raw = events_pareto_map.get(unit, {})
            unit_events = []
            for evt_status, evt_durasi in sorted(unit_events_raw.items(), key=lambda x: x[1], reverse=True):
                unit_events.append({
                    "status": evt_status,
                    "code": 0,
                    "hours": round(evt_durasi, 2)
                })
            
            total_delay = sum(e['hours'] for e in unit_events)
            kpi['events_pareto'] = {
                "total_delay_hours": round(total_delay, 2),
                "items": unit_events
            }
            
            results.append(kpi)
            
        return results
