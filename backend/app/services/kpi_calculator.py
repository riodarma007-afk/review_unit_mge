import pandas as pd
import numpy as np
from typing import Dict, Any

from app.core.kpi_targets import KPI_TARGETS, MECHANICAL_CODES

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
    def summarize_kpi(df_utama: pd.DataFrame, df_events: pd.DataFrame) -> Dict[str, Any]:
        """Hitung KPI level grup (summary total)"""
        if df_utama.empty:
            return KpiCalculator.calculate_kpi_from_aggs(0, 0, 0, 0, 0)
            
        sum_mohh = df_utama['MOHH'].sum() if 'MOHH' in df_utama else 0
        sum_downtime = df_utama['Downtime'].sum() if 'Downtime' in df_utama else 0
        sum_wh = df_utama['WH'].sum() if 'WH' in df_utama else 0
        sum_ritasi = df_utama['Ritasi'].sum() if 'Ritasi' in df_utama else 0
        
        sum_mech_downtime = 0
        if not df_events.empty and 'Status' in df_events and 'Durasi' in df_events:
            mech_events = df_events[df_events['Status'].isin(MECHANICAL_CODES)]
            sum_mech_downtime = mech_events['Durasi'].sum()
            
        return KpiCalculator.calculate_kpi_from_aggs(
            sum_mohh, sum_downtime, sum_mech_downtime, sum_wh, sum_ritasi
        )

    @staticmethod
    def calculate_trend(df_utama: pd.DataFrame, df_events: pd.DataFrame, group_by: str) -> pd.DataFrame:
        """
        Hitung trend KPI dengan group_by (Date, Shift, atau PIT).
        """
        if df_utama.empty:
            return pd.DataFrame()
            
        if group_by not in ['Date', 'Shift', 'PIT']:
            group_by = 'Date' # default
            
        # Agregasi data utama
        agg_funcs = {
            'MOHH': 'sum',
            'Downtime': 'sum',
            'WH': 'sum',
            'Ritasi': 'sum'
        }
        df_grouped = df_utama.groupby(group_by, as_index=False).agg(agg_funcs)
        
        # Agregasi mech downtime dari event
        mech_downtime_map = {}
        if not df_events.empty:
            mech_events = df_events[df_events['Status'].isin(MECHANICAL_CODES)]
            if not mech_events.empty:
                # Merge events dengan data_utama untuk mendapatkan field group_by (seperti Date, Shift, PIT)
                # karena event hanya punya ID_data_Input
                if group_by in mech_events.columns: # jika sudah di-join
                    mech_grouped = mech_events.groupby(group_by, as_index=False)['Durasi'].sum()
                    mech_downtime_map = dict(zip(mech_grouped[group_by], mech_grouped['Durasi']))
                else:
                    # Kita harus gabungkan dengan data utama
                    merged = pd.merge(mech_events, df_utama[['ID_data', group_by]], left_on='ID_data_Input', right_on='ID_data', how='inner')
                    mech_grouped = merged.groupby(group_by, as_index=False)['Durasi'].sum()
                    mech_downtime_map = dict(zip(mech_grouped[group_by], mech_grouped['Durasi']))
        
        results = []
        for _, row in df_grouped.iterrows():
            key = row[group_by]
            mech_dt = mech_downtime_map.get(key, 0)
            kpi = KpiCalculator.calculate_kpi_from_aggs(
                row['MOHH'], row['Downtime'], mech_dt, row['WH'], row['Ritasi']
            )
            # Konversi key ke string jika date
            key_str = str(key)
            kpi['label'] = key_str
            results.append(kpi)
            
        return pd.DataFrame(results)

    @staticmethod
    def calculate_unit_ranking(df_utama: pd.DataFrame, df_events: pd.DataFrame, metric: str = 'productivity') -> pd.DataFrame:
        """Hitung ranking unit berdasarkan metrik tertentu"""
        if df_utama.empty:
            return pd.DataFrame(columns=['unit_code', 'value'])
            
        df_grouped = df_utama.groupby('Unit_Code', as_index=False).agg({
            'MOHH': 'sum', 'Downtime': 'sum', 'WH': 'sum', 'Ritasi': 'sum'
        })
        
        mech_downtime_map = {}
        if not df_events.empty:
            mech_events = df_events[df_events['Status'].isin(MECHANICAL_CODES)]
            if not mech_events.empty:
                merged = pd.merge(mech_events, df_utama[['ID_data', 'Unit_Code']], left_on='ID_data_Input', right_on='ID_data', how='inner')
                mech_grouped = merged.groupby('Unit_Code', as_index=False)['Durasi'].sum()
                mech_downtime_map = dict(zip(mech_grouped['Unit_Code'], mech_grouped['Durasi']))
                
        results = []
        for _, row in df_grouped.iterrows():
            unit = row['Unit_Code']
            mech_dt = mech_downtime_map.get(unit, 0)
            kpi = KpiCalculator.calculate_kpi_from_aggs(
                row['MOHH'], row['Downtime'], mech_dt, row['WH'], row['Ritasi']
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
                
            results.append({'unit_code': unit, 'value': value})
            
        df_res = pd.DataFrame(results)
        # Drop unit yang valuenya None sebelum di-sort
        df_res = df_res.dropna(subset=['value'])
        return df_res

    @staticmethod
    def calculate_all_units_kpi(df_utama: pd.DataFrame, df_events: pd.DataFrame) -> list:
        """Hitung KPI lengkap untuk semua unit, mengembalikan list of dict"""
        if df_utama.empty:
            return []
            
        df_grouped = df_utama.groupby('Unit_Code', as_index=False).agg({
            'MOHH': 'sum', 'Downtime': 'sum', 'WH': 'sum', 'Ritasi': 'sum', 'Date': 'nunique',
            'Delay': 'sum', 'Idle': 'sum'
        })
        
        mech_downtime_map = {}
        breakdown_count_map = {}
        events_pareto_map = {}
        category_idle_map = {}
        category_delay_map = {}
        category_downtime_map = {}
        
        # Activity Breakdown
        activity_grouped = df_utama.groupby(['Unit_Code', 'Activity'], as_index=False).agg(
            Total_Ritasi=('Ritasi', 'sum'),
            Total_Shifts=('Date', 'count')
        )
        activity_map = {}
        for unit_val, group in activity_grouped.groupby('Unit_Code'):
            act_list = []
            for _, r in group.iterrows():
                act_list.append({
                    "activity": str(r['Activity']) if pd.notna(r['Activity']) else 'Unknown',
                    "ritasi": int(r['Total_Ritasi']),
                    "shifts": int(r['Total_Shifts'])
                })
            activity_map[unit_val] = act_list
        
        if not df_events.empty:
            merged = pd.merge(df_events, df_utama[['ID_data', 'Unit_Code']], left_on='ID_data_Input', right_on='ID_data', how='inner')
            
            # Aggregate categories for Idle, Delay, Downtime from actual events
            if 'Category' in merged.columns:
                cat_grouped = merged.groupby(['Unit_Code', 'Category'], as_index=False)['Durasi'].sum()
                for _, r in cat_grouped.iterrows():
                    unit = r['Unit_Code']
                    cat = str(r['Category']).strip().lower()
                    val = r['Durasi']
                    if cat == 'downtime':
                        category_downtime_map[unit] = val
                    elif cat == 'delay':
                        category_delay_map[unit] = val
                    elif cat == 'idle':
                        category_idle_map[unit] = val
            
            # Parekan events per unit (exclude Other, No timesheet, Holiday)
            merged_for_pareto = merged[merged['Durasi'] > 0].copy()
            merged_for_pareto['status_clean'] = merged_for_pareto['Status'].astype(str).str.strip().str.lower()
            exclude_statuses = ['other', 'others', 'no timesheet', 'holiday']
            events_filtered = merged_for_pareto[~merged_for_pareto['status_clean'].isin(exclude_statuses)]
            
            events_grouped = events_filtered.groupby(['Unit_Code', 'Status'], as_index=False)['Durasi'].sum()
            for unit, group in events_grouped.groupby('Unit_Code'):
                sorted_events = group.sort_values(by='Durasi', ascending=False)
                events_pareto_map[unit] = [
                    {
                        "status": row['Status'], 
                        "code": 0, 
                        "hours": round(row['Durasi'], 2)
                    }
                    for _, row in sorted_events.iterrows()
                ]

            mech_events = df_events[df_events['Status'].isin(MECHANICAL_CODES)]
            if not mech_events.empty:
                merged_mech = pd.merge(mech_events, df_utama[['ID_data', 'Unit_Code']], left_on='ID_data_Input', right_on='ID_data', how='inner')
                mech_grouped = merged_mech.groupby('Unit_Code', as_index=False).agg(
                    Durasi=('Durasi', 'sum'),
                    EventCount=('ID_data_Input', 'count')
                )
                mech_downtime_map = dict(zip(mech_grouped['Unit_Code'], mech_grouped['Durasi']))
                breakdown_count_map = dict(zip(mech_grouped['Unit_Code'], mech_grouped['EventCount']))
                
        results = []
        for _, row in df_grouped.iterrows():
            unit = row['Unit_Code']
            mech_dt = mech_downtime_map.get(unit, 0)
            # Override downtime with actual event sum if exists, else fallback to raw data
            real_downtime = category_downtime_map.get(unit, row['Downtime'])
            real_delay = category_delay_map.get(unit, row.get('Delay', 0))
            real_idle = category_idle_map.get(unit, row.get('Idle', 0))
            
            kpi = KpiCalculator.calculate_kpi_from_aggs(
                row['MOHH'], real_downtime, mech_dt, row['WH'], row['Ritasi']
            )
            kpi['unit_code'] = unit
            kpi['mohh'] = round(row['MOHH'], 2)
            kpi['wh'] = round(row['WH'], 2)
            kpi['downtime'] = round(real_downtime, 2)
            kpi['delay'] = round(real_delay, 2)
            kpi['idle'] = round(real_idle, 2)
            kpi['mech_downtime'] = round(mech_dt, 2)
            kpi['breakdown_count'] = int(breakdown_count_map.get(unit, 0))
            
            days_count = row.get('Date', 1)
            total_rit = row.get('Ritasi', 0)
            kpi['avg_ritasi_per_day'] = round(total_rit / days_count, 1) if days_count > 0 else 0
            
            kpi['activities'] = activity_map.get(unit, [])
            
            unit_events = events_pareto_map.get(unit, [])
            total_delay = sum(e['hours'] for e in unit_events)
            kpi['events_pareto'] = {
                "total_delay_hours": round(total_delay, 2),
                "items": unit_events
            }
            
            results.append(kpi)
            
        return results
