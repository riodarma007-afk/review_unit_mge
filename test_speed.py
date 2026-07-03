import requests
import time

BASE = 'http://localhost:8000/api/v1'

# Use a session to reuse TCP connection
session = requests.Session()

# Warm up - make initial calls (cold)
print("=== Warming up (cold calls) ===")
s = time.time()
session.get(f'{BASE}/fuel/unit', params={'unit_code': 'GHT 743', 'date_from': '2026-06-23', 'date_to': '2026-06-23'})
print(f"  Fuel warm-up: {time.time()-s:.3f}s")

s = time.time()
session.get(f'{BASE}/hauling/unit', params={'unit_code': 'GHT 743', 'date_from': '2026-06-23', 'date_to': '2026-06-23'})
print(f"  Hauling warm-up: {time.time()-s:.3f}s")

# Now test cached with reused connection
print("\n=== Cached calls (reused TCP connection) ===")
for i in range(3):
    s = time.time()
    r = session.get(f'{BASE}/fuel/unit', params={'unit_code': 'GHT 743', 'date_from': '2026-06-23', 'date_to': '2026-06-23'})
    fuel_t = time.time() - s
    
    s = time.time()
    r2 = session.get(f'{BASE}/hauling/unit', params={'unit_code': 'GHT 743', 'date_from': '2026-06-23', 'date_to': '2026-06-23'})
    haul_t = time.time() - s
    
    print(f"  Run {i+1}: Fuel={fuel_t:.3f}s  Hauling={haul_t:.3f}s")

# Test different unit (cold for that unit)
print("\n=== Different unit (cold) ===")
s = time.time()
r3 = session.get(f'{BASE}/fuel/unit', params={'unit_code': 'GHT 748', 'date_from': '2026-06-23', 'date_to': '2026-06-23'})
print(f"  GHT 748 fuel cold: {time.time()-s:.3f}s  status: {r3.status_code}")

# Cached for that unit
s = time.time()
r4 = session.get(f'{BASE}/fuel/unit', params={'unit_code': 'GHT 748', 'date_from': '2026-06-23', 'date_to': '2026-06-23'})
print(f"  GHT 748 fuel cached: {time.time()-s:.3f}s")
