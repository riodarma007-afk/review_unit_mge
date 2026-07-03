import requests
import json

API_KEY = "mge_fuel_3m9gzdIRGQf2AFtq7PeYSBNxiZLJrcky6nXuKhDWoHMEwlj4"
BASE_URL = "https://planning.mge.co.id/api/portal/fuel"

# Fetch fuel data for June 2026 and look for MGE vendor units (GHT/GMT)
resp = requests.get(
    BASE_URL,
    headers={"X-API-Key": API_KEY},
    params={"date_from": "2026-06-01", "date_to": "2026-06-30", "vendor": "MGE", "limit": 500, "page": 1},
    timeout=15
)

body = resp.json()
meta = body.get("meta", {})
data = body.get("data", [])

print(f"=== MGE vendor: {meta.get('total', 0)} records ===\n")

if data:
    # Collect unique unit_code and unit_fix
    units_info = {}
    for row in data:
        uc = row.get('unit_code', '')
        uf = row.get('unit_fix', '')
        ut = row.get('unit_type', '')
        um = row.get('unit_model', '')
        if uc not in units_info:
            units_info[uc] = {'unit_fix': uf, 'unit_type': ut, 'unit_model': um, 'count': 0}
        units_info[uc]['count'] += 1
    
    print(f"=== Unique units from MGE vendor ({len(units_info)}) ===")
    print(f"{'unit_code':25s} | {'unit_fix':15s} | {'unit_type':15s} | {'unit_model':15s} | count")
    print("-" * 95)
    for uc, info in sorted(units_info.items()):
        print(f"{uc:25s} | {info['unit_fix']:15s} | {info['unit_type']:15s} | {info['unit_model']:15s} | {info['count']}")
else:
    print("No MGE vendor data found")

# Also try searching for GHT specifically
print("\n\n=== Searching for GHT units ===")
resp2 = requests.get(
    BASE_URL,
    headers={"X-API-Key": API_KEY},
    params={"date_from": "2026-06-01", "date_to": "2026-06-30", "search": "GHT", "limit": 500, "page": 1},
    timeout=15
)
body2 = resp2.json()
meta2 = body2.get("meta", {})
data2 = body2.get("data", [])
print(f"GHT search: {meta2.get('total', 0)} records")

if data2:
    units_ght = {}
    for row in data2:
        uc = row.get('unit_code', '')
        uf = row.get('unit_fix', '')
        if uc not in units_ght:
            units_ght[uc] = {'unit_fix': uf, 'count': 0, 'vendor': row.get('vendor', '')}
        units_ght[uc]['count'] += 1
    
    print(f"\nUnique GHT units ({len(units_ght)}):")
    for uc, info in sorted(units_ght.items()):
        print(f"  fuel.unit_code = '{uc}' | fuel.unit_fix = '{info['unit_fix']}' | vendor = '{info['vendor']}' | records = {info['count']}")

# Also try searching for GMT
print("\n\n=== Searching for GMT units ===")
resp3 = requests.get(
    BASE_URL,
    headers={"X-API-Key": API_KEY},
    params={"date_from": "2026-06-01", "date_to": "2026-06-30", "search": "GMT", "limit": 500, "page": 1},
    timeout=15
)
body3 = resp3.json()
meta3 = body3.get("meta", {})
data3 = body3.get("data", [])
print(f"GMT search: {meta3.get('total', 0)} records")

if data3:
    units_gmt = {}
    for row in data3:
        uc = row.get('unit_code', '')
        uf = row.get('unit_fix', '')
        if uc not in units_gmt:
            units_gmt[uc] = {'unit_fix': uf, 'count': 0, 'vendor': row.get('vendor', '')}
        units_gmt[uc]['count'] += 1
    
    print(f"\nUnique GMT units ({len(units_gmt)}):")
    for uc, info in sorted(units_gmt.items()):
        print(f"  fuel.unit_code = '{uc}' | fuel.unit_fix = '{info['unit_fix']}' | vendor = '{info['vendor']}' | records = {info['count']}")

# Now show how OpTrack names units - looking at the image filenames
print("\n\n=== OpTrack unit naming (from image files) ===")
import os
img_dir = r"e:\project rio\Dashboard_optrack\frontend\public\units"
if os.path.exists(img_dir):
    files = sorted(os.listdir(img_dir))[:20]
    for f in files:
        print(f"  OpTrack image: {f}")
