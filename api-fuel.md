# API Fuel — Dokumentasi

Base URL production: `https://planning.mge.co.id/api/portal`

---

## Autentikasi

Semua request wajib menyertakan salah satu header berikut:

| Metode | Header | Nilai |
|--------|--------|-------|
| API Key | `X-API-Key` | `<api_key>` |
| JWT | `Authorization` | `Bearer <token>` |

API Key digunakan untuk akses machine-to-machine (project lain). JWT digunakan oleh web app setelah login.

---

## Endpoint

### `GET /fuel`

Mengambil daftar data fuel dengan pagination server-side.

#### Query Parameters

| Parameter | Tipe | Default | Keterangan |
|-----------|------|---------|------------|
| `page` | integer | `1` | Nomor halaman |
| `limit` | integer | `100` | Jumlah data per halaman (maks: 500) |
| `date_from` | string | — | Filter tanggal mulai, format `YYYY-MM-DD` (inklusif) |
| `date_to` | string | — | Filter tanggal akhir, format `YYYY-MM-DD` (inklusif) |
| `shift` | string | — | Filter shift, contoh: `DAY`, `NIGHT` |
| `vendor` | string | — | Filter vendor (exact match) |
| `unit_type` | string | — | Filter tipe unit (exact match) |
| `alocation` | string | — | Filter alokasi (exact match) |
| `location` | string | — | Filter lokasi (exact match) |
| `search` | string | — | Pencarian teks di kolom: `unit_code`, `vendor`, `operator`, `location` |

#### Contoh Request

```bash
# cURL
curl "https://planning.mge.co.id/api/portal/fuel?date_from=2026-06-01&date_to=2026-06-30&limit=500" \
  -H "X-API-Key: <api_key>"
```

```js
// JavaScript (fetch)
const res = await fetch(
  'https://planning.mge.co.id/api/portal/fuel?date_from=2026-06-01&date_to=2026-06-30&limit=500',
  { headers: { 'X-API-Key': process.env.MGE_API_KEY } }
)
const { data, meta } = await res.json()
```

```python
# Python (requests)
import requests

resp = requests.get(
  'https://planning.mge.co.id/api/portal/fuel',
  headers={'X-API-Key': '<api_key>'},
  params={'date_from': '2026-06-01', 'date_to': '2026-06-30', 'limit': 500}
)
rows = resp.json()['data']
```

#### Response

```json
{
  "data": [
    {
      "id": "1234567",
      "unit_fix": "DT-001",
      "date": "2026-06-01T00:00:00.000Z",
      "periode": "JUNI 2026",
      "shift": "DAY",
      "time": "07:30:00",
      "reg_no": "KT1234AB",
      "unit_code": "HD785-01",
      "unit_model": "HD785-7",
      "unit_type": "DUMP TRUCK",
      "brand": "KOMATSU",
      "vendor": "MGE",
      "alocation": "OB",
      "km": null,
      "hm": "5234.50",
      "fm_awal": "102300",
      "fm_akhir": "102450",
      "refueling": "150.00",
      "source": "TANGKI",
      "location": "WORKSHOP",
      "operator": "BUDI SANTOSO",
      "fuelman": "AHMAD YANI",
      "no_voucher": "VCR-2026-0001",
      "batch_id": "98"
    }
  ],
  "meta": {
    "total": 6530,
    "page": 1,
    "limit": 500,
    "totalPages": 14
  }
}
```

---

## Mengambil Semua Data

Limit maksimal per request adalah **500 baris**. Untuk mengambil semua data, iterasi halaman menggunakan `meta.totalPages`.

### JavaScript

```js
async function fetchAllFuel(params = {}) {
  const BASE = 'https://planning.mge.co.id/api/portal/fuel'
  const headers = { 'X-API-Key': process.env.MGE_API_KEY }
  const rows = []
  let page = 1

  while (true) {
    const url = `${BASE}?${new URLSearchParams({ ...params, page, limit: 500 })}`
    const { data, meta } = await fetch(url, { headers }).then(r => r.json())
    rows.push(...data)
    if (page >= meta.totalPages) break
    page++
  }

  return rows
}

// Contoh: ambil semua data Juni 2026
const data = await fetchAllFuel({ date_from: '2026-06-01', date_to: '2026-06-30' })
```

### Python

```python
import requests

def fetch_all_fuel(api_key, **params):
    BASE = 'https://planning.mge.co.id/api/portal/fuel'
    headers = {'X-API-Key': api_key}
    rows = []
    page = 1

    while True:
        resp = requests.get(BASE, headers=headers, params={**params, 'page': page, 'limit': 500})
        body = resp.json()
        rows.extend(body['data'])
        if page >= body['meta']['totalPages']:
            break
        page += 1

    return rows

# Contoh: ambil semua data Juni 2026
data = fetch_all_fuel(
    api_key='<api_key>',
    date_from='2026-06-01',
    date_to='2026-06-30'
)
```

### PHP

```php
function fetchAllFuel(string $apiKey, array $params = []): array {
    $base = 'https://planning.mge.co.id/api/portal/fuel';
    $rows = [];
    $page = 1;

    do {
        $query = http_build_query(array_merge($params, ['page' => $page, 'limit' => 500]));
        $ctx  = stream_context_create(['http' => [
            'header' => "X-API-Key: $apiKey\r\n",
        ]]);
        $body = json_decode(file_get_contents("$base?$query", false, $ctx), true);
        $rows = array_merge($rows, $body['data']);
        $totalPages = $body['meta']['totalPages'];
        $page++;
    } while ($page <= $totalPages);

    return $rows;
}

// Contoh: ambil semua data Juni 2026
$data = fetchAllFuel('<api_key>', ['date_from' => '2026-06-01', 'date_to' => '2026-06-30']);
```

---

## Error Response

| HTTP Status | Kondisi |
|-------------|---------|
| `401` | API Key tidak valid atau tidak dikirim |
| `500` | Error internal server |

```json
{ "message": "API Key tidak valid" }
```
