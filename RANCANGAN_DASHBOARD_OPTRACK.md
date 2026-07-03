# Rancangan Teknis: Dashboard OPTRACK — Hauling & Overburden Performance

**Dokumen untuk:** Agent eksekusi kode (Antigravity)
**Disusun oleh:** Data Analyst (Departemen Produksi)
**Tanggal:** 28 Juni 2026
**Versi:** 1.0

---

## 1. Latar belakang dan tujuan

Perusahaan memiliki sistem tracking operasi tambang bernama **OPTRACK**, yang mencatat performa unit hauling (Dump Truck) untuk aktivitas **Hauling** dan **OB (Overburden)** secara real-time per shift. Data tersimpan di MySQL (hosting cPanel) dengan 3 tabel utama.

Tujuan proyek ini: membangun **dashboard web modern** yang menampilkan KPI standar tambang batu bara (MA, PA, UA, EU, produktivitas, dan analisis delay) dengan visualisasi interaktif dan animasi halus, supaya tim produksi bisa memantau performa unit hauling secara cepat dan akurat.

### Tech stack yang ditetapkan

| Layer | Teknologi |
|---|---|
| Database | MySQL (remote, hosting cPanel) |
| Backend | Python — FastAPI, Pandas, NumPy, SQLAlchemy, PyMySQL |
| Frontend | Vue.js 3 (Composition API) + Vite |
| Visualisasi | ApexCharts (vue3-apexcharts) sebagai chart utama |
| State management | Pinia |
| HTTP client | Axios |
| Environment | Local development (laptop), MySQL diakses remote |

---

## 2. Analisis struktur data sumber

Sample data yang dianalisis: `optrack_27.xlsx` (export dari MySQL, data 1 hari, 27 Juni 2026, 60 unit).

### 2.1 Tabel `data_utama` (1 baris = 1 unit, 1 shift, 1 hari)

| Kolom | Tipe | Keterangan |
|---|---|---|
| `ID_data` | string (UUID) | Primary key |
| `Date` | date | Tanggal operasi |
| `Shift` | string | `Day` / `Night` |
| `PIT` | string | Lokasi tambang, contoh: `North JO IC`, `South JO IC` |
| `Unit_Code` | string | Kode unit, contoh: `GHT 701`, `GMT 721` |
| `Operator` | string | Nama operator |
| `Activity` | string | `Hauling` atau `OB` (Overburden) |
| `HM_Awal`, `HM_Akhir` | float | Hour meter awal/akhir |
| `Ritasi` | integer | Jumlah rit/trip |
| `HM` | float | `HM_Akhir - HM_Awal` |
| `MOHH` | float | Mine Operating Hour (jam kerja tambang tersedia, biasanya 12 jam/shift) |
| `WH` | float | Working Hour = `MOHH - Downtime - Delay - Idle` (**tervalidasi exact match**) |
| `Downtime` | float | Jam unit rusak/maintenance (jam) |
| `Delay` | float | Jam delay operasional non-mekanikal (jam) |
| `Idle` | integer | Jam idle (saat ini selalu 0 di sample, tapi kolom harus tetap diakomodasi) |
| `last_modified` | datetime (string) | Timestamp update terakhir |
| `is_deleted` | integer (0/1) | Soft-delete flag — **WAJIB difilter `is_deleted = 0` di semua query** |

### 2.2 Tabel `laporan_event` (1 baris = 1 kejadian/event, banyak per unit per shift)

| Kolom | Tipe | Keterangan |
|---|---|---|
| `Event_ID` | string (UUID) | Primary key |
| `ID_data_Input` | string (UUID) | Foreign key → `data_utama.ID_data` |
| `Date`, `Shift`, `Unit Code`, `User`, `Activity`, `PIT` | — | Duplikasi kontekstual dari `data_utama` |
| `Time` | string | Jam blok 1 jam, format `"HH - HH"` (contoh `"06 - 07"`) |
| `Code` | integer | Kode numerik event (lihat tabel mapping di 2.3) |
| `Status` | string | Nama event (lihat tabel mapping di 2.3) |
| `Start`, `Stop` | string (HH:MM) | Jam mulai/selesai event |
| `Plan` | integer | Kode rencana (durasi target dalam menit, observasi: 0,1,2,3,4,5,6,10) |
| `Durasi` | float | Durasi event dalam jam — **total per unit per shift = `Delay + Downtime` (tervalidasi exact match)** |
| `Noted` | string (nullable) | Catatan tambahan |

### 2.3 Mapping kode event → kategori KPI (disepakati dengan user)

Aturan klasifikasi **MA vs Delay operasional** sudah dikonfirmasi user sesuai standar perusahaan:

```
KATEGORI MEKANIKAL (mempengaruhi MA — Mechanical Availability):
  - Code 52 → "Schedule Maintanance"
  - Code 53 → "Unshedule Maintanance"

KATEGORI DELAY OPERASIONAL (mempengaruhi UA, tidak mempengaruhi MA):
  - Semua status lainnya, termasuk namun tidak terbatas pada:
    Antri Loading, Antri Hopper, Antri Dumping, P5M, P2H, Change Shift,
    Meal & Rest, Check Fatique, Jam Tanggung, Refueling, Others,
    No Operator, Waiting Loader_No Opr, Waiting Loader_Breakdown,
    Change PIT, Lambat Start, Waiting Expose, Moving Front, Praying,
    Streaching, Force Majour, Waiting Instruction, Prepare Front
```

> **Catatan penting untuk agent:** daftar status di atas adalah hasil observasi dari sample data 1 hari. Mapping kode → status **harus dibaca dinamis dari tabel**, bukan di-hardcode sebagai enum tertutup — gunakan `Code` sebagai kunci klasifikasi mekanikal (`Code IN (52, 53)`), bukan mencocokkan string `Status` (rawan typo/variasi penulisan, contoh: "Unshedule" salah ketik dari "Unscheduled").

### 2.4 Tabel `summary`

Identik dengan `data_utama` minus kolom `PIT` dan `Activity`. **Keputusan desain:** backend tidak perlu query tabel ini secara terpisah — semua kebutuhan summary dapat dihasilkan dari agregasi `data_utama`. Tabel ini diasumsikan view/rekap yang dibuat sistem OPTRACK sendiri, bukan sumber data tambahan.

### 2.5 Relasi antar tabel

```
data_utama.ID_data  1 ---- N  laporan_event.ID_data_Input
```

Relasi tervalidasi 100% konsisten di sample data (lihat hasil validasi di bagian 3).

---

## 3. Definisi formula KPI (kontrak antara backend dan frontend)

Seluruh formula berikut **wajib diimplementasikan di layer `services/kpi_calculator.py`**, bukan di SQL maupun di-hardcode di frontend. Ini satu-satunya sumber kebenaran rumus.

| KPI | Formula | Catatan |
|---|---|---|
| **PA** (Physical Availability) | `(MOHH − Downtime) / MOHH × 100%` | Ketersediaan fisik unit (lepas dari delay operasional) |
| **MA** (Mechanical Availability) | `(MOHH − mechanical_downtime) / MOHH × 100%`, dengan `mechanical_downtime = SUM(Durasi)` dari event `Code IN (52, 53)` | Lihat 2.3 |
| **UA** (Use of Availability) | `WH / (MOHH − Downtime) × 100%` | Seberapa efektif unit yang tersedia secara fisik benar-benar dipakai |
| **EU** (Effective Utilization) | `WH / MOHH × 100%` | Utilisasi total terhadap jam tersedia |
| **Productivity** | `Ritasi / WH` (rit per jam kerja) | Hindari pembagian oleh nol — jika `WH = 0`, hasil `null`, bukan error |
| **Delay ratio** | `Delay / MOHH × 100%` | |
| **Idle ratio** | `Idle / MOHH × 100%` | |

### Target KPI default (standar industri, dapat diubah via konfigurasi)

Belum ada target resmi dari perusahaan — gunakan default berikut sebagai garis pembanding di chart, ditempatkan sebagai **konstanta yang mudah diubah** (`backend/app/core/kpi_targets.py`), bukan hardcode di komponen Vue:

```python
KPI_TARGETS = {
    "MA": 85.0,   # %
    "PA": 90.0,   # %
    "UA": 80.0,   # %
    "EU": 70.0,   # %
}
```

> Tandai jelas di UI (misal label kecil "target default industri") bahwa angka ini bukan standar resmi perusahaan, supaya tidak disalahartikan sebagai target final saat divalidasi ke pihak lain.

### Aturan agregasi (penting untuk konsistensi)

KPI **tidak boleh dirata-rata langsung antar unit** (`AVERAGE(MA_unit1, MA_unit2, ...)` salah secara matematis). Saat menampilkan KPI gabungan (semua unit / per PIT / per shift), backend harus:

1. Sum dahulu komponen mentah (`SUM(MOHH)`, `SUM(Downtime)`, `SUM(mechanical_downtime)`, `SUM(WH)`, `SUM(Ritasi)`) pada level agregasi yang diminta
2. Baru hitung rasio dari hasil sum tersebut

Ini berlaku di semua endpoint yang mengembalikan KPI level grup (overview, trend, per-PIT, per-shift).

---

## 4. Arsitektur sistem

```
┌─────────────────────────────────────────────────────────┐
│  MySQL (cPanel, remote)                                  │
│  Tabel: data_utama, laporan_event, summary               │
└───────────────────────┬───────────────────────────────────┘
                         │ SQLAlchemy + PyMySQL
┌────────────────────────▼──────────────────────────────────┐
│  Backend — FastAPI                                         │
│  ┌────────────┐   ┌──────────────────┐   ┌──────────────┐ │
│  │ Repository │ → │ Service/KPI engine│ → │ Router (API) │ │
│  │ (raw query)│   │ (pandas, numpy)   │   │ (REST+JSON)  │ │
│  └────────────┘   └──────────────────┘   └──────────────┘ │
└────────────────────────┬──────────────────────────────────┘
                         │ HTTP (Axios)
┌────────────────────────▼──────────────────────────────────┐
│  Frontend — Vue.js 3 + ApexCharts + Pinia                  │
│  Views → Components → Composables → API service            │
└─────────────────────────────────────────────────────────────┘
```

**Prinsip clean code yang wajib diikuti agent:**

1. **Separation of concerns ketat**: repository tidak boleh memuat logic bisnis; service tidak boleh memuat SQL mentah; router tidak boleh memuat kalkulasi.
2. **Single source of truth untuk formula**: semua rumus KPI hanya ada di `kpi_calculator.py`.
3. **Tidak ada angka magic**: target KPI, kode event mekanikal (52, 53), dan konstanta lain harus berupa named constant di `core/`, bukan literal tersebar di kode.
4. **Type hints wajib** di semua fungsi Python; **Pydantic schema** wajib untuk setiap response API (jangan return `dict` mentah).
5. **Komponen Vue kecil dan fokus**: 1 komponen = 1 tanggung jawab visual. Logic fetch data tidak boleh ditulis langsung di dalam komponen — gunakan composables atau Pinia store.
6. **Penamaan konsisten**: backend pakai `snake_case` untuk field internal, response API tetap `snake_case` di JSON (frontend mapping di service layer Axios jika butuh `camelCase`).

---

## 5. Struktur folder proyek

```
optrack-dashboard/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py              # Pydantic Settings (.env)
│   │   │   ├── database.py            # SQLAlchemy engine + session
│   │   │   └── kpi_targets.py         # konstanta target KPI & kode event
│   │   ├── models/
│   │   │   └── optrack.py             # SQLAlchemy ORM: DataUtama, LaporanEvent
│   │   ├── schemas/
│   │   │   ├── kpi.py                 # Pydantic: KpiSummaryResponse, dll
│   │   │   ├── unit.py
│   │   │   └── event.py
│   │   ├── repositories/
│   │   │   └── optrack_repository.py  # query murni, return DataFrame/list ORM
│   │   ├── services/
│   │   │   ├── kpi_calculator.py      # rumus MA/PA/UA/EU/productivity
│   │   │   └── delay_analysis.py      # pareto delay per Status/Code
│   │   ├── routers/
│   │   │   ├── kpi.py
│   │   │   ├── units.py
│   │   │   ├── events.py
│   │   │   └── filters.py
│   │   └── utils/
│   │       └── date_helpers.py
│   ├── tests/
│   │   ├── test_kpi_calculator.py     # unit test rumus dengan data sample
│   │   └── test_delay_analysis.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/index.js
│   │   ├── stores/
│   │   │   ├── filterStore.js         # filter global: tanggal, shift, PIT, unit
│   │   │   └── kpiStore.js
│   │   ├── services/
│   │   │   └── apiClient.js           # axios instance, base URL dari .env
│   │   ├── composables/
│   │   │   ├── useKpiSummary.js
│   │   │   ├── useDelayPareto.js
│   │   │   └── useAnimatedCounter.js  # animasi count-up angka KPI
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── AppSidebar.vue
│   │   │   │   └── AppTopBar.vue
│   │   │   ├── kpi/
│   │   │   │   ├── KpiCard.vue
│   │   │   │   └── KpiRadialGauge.vue
│   │   │   ├── charts/
│   │   │   │   ├── TrendLineChart.vue
│   │   │   │   ├── DelayParetoChart.vue
│   │   │   │   ├── UnitRankingBarChart.vue
│   │   │   │   └── ShiftHeatmapChart.vue
│   │   │   └── common/
│   │   │       ├── GlobalFilterBar.vue
│   │   │       ├── DataTable.vue
│   │   │       └── LoadingSkeleton.vue
│   │   ├── views/
│   │   │   ├── OverviewView.vue
│   │   │   ├── UnitDetailView.vue
│   │   │   └── DelayAnalysisView.vue
│   │   └── assets/styles/main.css
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
│
├── docker-compose.yml         # opsional untuk deployment lanjutan
├── .gitignore
└── README.md
```

---

## 6. Kontrak API (backend ⇄ frontend)

Base URL: `/api/v1`

Semua endpoint list mendukung query parameter filter berikut (opsional, default = semua data):

```
?date_from=2026-06-01&date_to=2026-06-27&shift=Day&pit=North%20JO%20IC&unit_code=GHT%20701&activity=Hauling
```

### 6.1 `GET /api/v1/filters/options`
Mengembalikan opsi dropdown filter (daftar unit, PIT, shift, activity, rentang tanggal tersedia).

```json
{
  "units": ["GHT 701", "GHT 702", "..."],
  "pits": ["North JO IC", "South JO IC"],
  "shifts": ["Day", "Night"],
  "activities": ["Hauling", "OB"],
  "date_range": { "min": "2026-06-01", "max": "2026-06-27" }
}
```

### 6.2 `GET /api/v1/kpi/summary`
KPI gabungan (untuk kartu KPI di atas dashboard). Dihitung sesuai aturan agregasi di bagian 3.

```json
{
  "period": { "date_from": "2026-06-27", "date_to": "2026-06-27" },
  "ma_percent": 92.5,
  "pa_percent": 96.1,
  "ua_percent": 81.3,
  "eu_percent": 78.4,
  "total_ritasi": 412,
  "productivity_rit_per_hour": 1.18,
  "unit_count": 60,
  "targets": { "ma": 85.0, "pa": 90.0, "ua": 80.0, "eu": 70.0 }
}
```

### 6.3 `GET /api/v1/kpi/trend?group_by=date|shift|pit`
Data time-series untuk line/area chart.

```json
{
  "group_by": "date",
  "series": [
    { "label": "2026-06-25", "ma_percent": 88.2, "pa_percent": 94.0, "ua_percent": 79.1, "eu_percent": 75.0 },
    { "label": "2026-06-26", "ma_percent": 90.1, "pa_percent": 95.3, "ua_percent": 80.5, "eu_percent": 76.8 }
  ]
}
```

### 6.4 `GET /api/v1/units/ranking?metric=productivity|ritasi|ma_percent&order=desc&limit=10`
Ranking unit untuk bar chart.

```json
{
  "metric": "productivity",
  "data": [
    { "unit_code": "GHT 715", "value": 1.45 },
    { "unit_code": "GHT 702", "value": 1.40 }
  ]
}
```

### 6.5 `GET /api/v1/delay/pareto`
Breakdown durasi delay per kategori event, terurut menurun, dengan kumulatif persentase (untuk pareto chart).

```json
{
  "total_delay_hours": 145.7,
  "items": [
    { "status": "Antri Loading", "code": 16, "hours": 38.2, "percent": 26.2, "cumulative_percent": 26.2 },
    { "status": "P2H", "code": 25, "hours": 22.4, "percent": 15.4, "cumulative_percent": 41.6 }
  ]
}
```

### 6.6 `GET /api/v1/units/{unit_code}/detail`
Drilldown 1 unit: KPI unit tersebut + daftar event mentah.

```json
{
  "unit_code": "GHT 701",
  "kpi": { "ma_percent": 100.0, "pa_percent": 100.0, "ua_percent": 75.5, "eu_percent": 75.5, "ritasi": 5 },
  "events": [
    { "time": "06 - 07", "status": "P5M", "start": "06:00", "stop": "06:10", "durasi_jam": 0.17 }
  ]
}
```

> **Catatan agent:** semua response wajib divalidasi lewat Pydantic `response_model`, bukan dict bebas — supaya error tipe data tertangkap di backend, bukan muncul aneh di frontend.

---

## 7. Rencana visual & komponen frontend

| Komponen | Chart/Visual | Library | Catatan animasi |
|---|---|---|---|
| `KpiCard.vue` | Angka besar MA/PA/UA/EU | CSS + composable `useAnimatedCounter` | Count-up 0 → nilai akhir, ease-out ~800ms, re-trigger saat filter berubah |
| `KpiRadialGauge.vue` | Radial bar per KPI dengan garis target | ApexCharts `radialBar` | Animasi default ApexCharts; warna dinamis: hijau (≥target), kuning (90–100% dari target), merah (<90% dari target) |
| `TrendLineChart.vue` | Line/area chart trend KPI per tanggal/shift | ApexCharts `line`/`area` | Smooth curve, gradient fill tipis, draw-in animation saat load |
| `DelayParetoChart.vue` | Bar (durasi) + line (kumulatif %) | ApexCharts mixed chart | Animasi bar grow dari bawah |
| `UnitRankingBarChart.vue` | Horizontal bar, top/bottom N unit | ApexCharts `bar` horizontal | Sort interaktif (productivity/ritasi/MA) |
| `ShiftHeatmapChart.vue` | Heatmap unit × shift untuk delay | ApexCharts `heatmap` | Warna intensitas delay |
| `GlobalFilterBar.vue` | Filter tanggal, shift, PIT, unit, activity | native + Pinia | Update semua chart reaktif via store |
| `LoadingSkeleton.vue` | Placeholder saat fetch | CSS shimmer | Transisi fade saat data masuk |

**Palet warna disarankan:** netral gelap untuk background dashboard (mode gelap industri tambang umum dipakai di control room), aksen warna semantik KPI (hijau/kuning/merah) supaya kontras dan mudah dipantau dari jarak monitor.

---

## 8. Konfigurasi koneksi database (keamanan)

- Kredensial MySQL **tidak boleh hardcode** — wajib via `.env` + `pydantic-settings`:

```env
# backend/.env (jangan commit ke git)
DB_HOST=103.58.102.44
DB_PORT=3306
DB_USER= mge_planning
DB_PASSWORD=PlanningMGE2026
DB_NAME= mge_planning_staging

List Database yang diambil
- Optrack_data_event : adalah data utama
- Optrack_breakdown_list : adalah database event unit seperti p5m dan lain lain
- optrack_summary_mohh : database summary dari data utama,
semua data saling berkaitan melalui ID nya, summary data memiliki relation to data utama melalui ID_data yang ditulis dengan nama unit tanggal dan shift, lalu data utama dengan data event memiliki relation through ID_data di data utama dan ID_data_input di data event.
```

- `backend/.env.example` disediakan tanpa nilai asli, sebagai template.
- `.gitignore` wajib mencantumkan `.env`.
- Koneksi pakai connection pooling SQLAlchemy (`pool_size`, `pool_recycle`) karena akses remote ke cPanel — hindari koneksi baru tiap request.
- Filter `is_deleted = 0` wajib ada di **semua** query repository terhadap `data_utama` — tidak boleh terlewat di endpoint manapun.

---

## 9. Tahapan eksekusi yang disarankan (untuk agent)

1. **Setup project skeleton** — folder backend & frontend, dependency install, `.env.example`
2. **Backend: koneksi DB + model + repository** — pastikan bisa `SELECT` dari ketiga tabel dengan kredensial yang akan diberikan user
3. **Backend: kpi_calculator.py + unit test** — pakai data sample (`optrack_27.xlsx`, sudah divalidasi rumusnya cocok) sebagai fixture test, supaya rumus benar sebelum sambung ke DB asli
4. **Backend: routers + schemas** — expose endpoint sesuai kontrak di bagian 6
5. **Backend: test manual via `/docs` (Swagger UI)** sebelum lanjut ke frontend
6. **Frontend: setup Vite + Vue 3 + Pinia + Axios + ApexCharts**
7. **Frontend: layout dasar (Sidebar, TopBar, routing)**
8. **Frontend: GlobalFilterBar + filterStore** — pondasi reaktivitas semua chart
9. **Frontend: KpiCard + KpiRadialGauge** (Overview view dulu)
10. **Frontend: chart-chart lain** (Trend, Pareto, Ranking, Heatmap)
11. **Frontend: UnitDetailView (drilldown)**
12. **Polish animasi, loading state, responsive layout**
13. **README final**: cara install, cara isi `.env`, cara jalankan (`uvicorn` + `npm run dev`)

---

## 10. Hal yang masih perlu konfirmasi/disediakan user sebelum produksi penuh

- Kredensial MySQL aktual (host, port, user, password, nama database) — **jangan dimasukkan ke dokumen ini**, serahkan langsung ke agent secara aman saat development (`.env` lokal).
- Nama tabel aktual di MySQL (asumsi sementara: `data_utama`, `laporan_event`, `summary` — sesuaikan dengan nama tabel asli di database).
- Apakah ada tabel master `unit` (spek unit: kapasitas tonase, model alat) yang belum terlihat di sample — relevan jika nanti mau hitung BCM/jam atau Match Factor dengan alat gali.
- Volume data riil (berapa hari/bulan riwayat tersimpan) — relevan untuk strategi pagination dan performa query trend jangka panjang.
- Target KPI resmi perusahaan (saat ini pakai default standar industri, lihat bagian 3).

---

*Dokumen ini disusun berdasarkan analisis sample data `optrack_27.xlsx` (1 hari operasi, 27 Juni 2026, 60 unit, 2 PIT, 2 shift, 2 aktivitas). Validasi formula `WH = MOHH − Downtime − Delay − Idle` dan `SUM(Durasi event) = Delay + Downtime` per unit per shift telah dilakukan dan cocok 100% terhadap sample data.*
