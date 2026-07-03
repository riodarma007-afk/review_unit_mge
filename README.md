# Optrack Dashboard

Optrack Dashboard adalah aplikasi *real-time monitoring* untuk melacak performa unit alat berat, penggunaan bahan bakar (Fuel), ritasi, dan analisis waktu tunda (*delay analysis*) yang dikembangkan untuk kebutuhan **Planning Department**.

## Arsitektur Aplikasi (Monorepo)

Proyek ini dibangun menggunakan arsitektur terpisah (*decoupled*) namun berada dalam satu *repository* (monorepo) agar memudahkan proses *deployment*:

- **Frontend (`/frontend`)**: Dibangun menggunakan **Vue 3**, **Vite**, dan **Pinia** untuk *state management*. Menangani antarmuka visual, filter interaktif, animasi grafik (menggunakan ApexCharts), dan pemanggilan API.
- **Backend (`/backend`)**: Dibangun menggunakan **Python** dengan kerangka kerja **FastAPI**. Bertugas sebagai "Mesin" pemroses logika bisnis, menghitung kalkulasi KPI, menarik data dari API pihak ketiga (Fuel & Hauling API), dan berkomunikasi dengan database MySQL menggunakan **SQLAlchemy**.
- **Serverless API (`/api`)**: Digunakan secara khusus sebagai *entrypoint* (titik masuk) bagi sistem Vercel Serverless Functions agar kode Python dapat berjalan langsung di *environment* Vercel.

## Konfigurasi & Kebutuhan (Prerequisites)

Untuk menjalankan proyek ini secara lokal, Anda membutuhkan:
1. **Node.js** (versi 16+ disarankan) untuk Frontend.
2. **Python** (versi 3.9+) untuk Backend.
3. File `backend/.env` (copy dari `backend/.env.example`) berisi kredensial database MySQL dan Fuel API — wajib diisi, tidak ada default di kode.

## Cara Menjalankan Secara Lokal (Development)

Proyek ini dapat dijalankan di perangkat lokal untuk kebutuhan *development* dan pengetesan.

### 1. Menjalankan Backend (FastAPI)
Buka terminal baru dan arahkan ke folder `backend`. Disarankan menggunakan *virtual environment* (`venv`):
```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash; PowerShell: venv\Scripts\Activate.ps1
pip install -r requirements.txt uvicorn
cp .env.example .env           # lalu isi kredensial DB & Fuel API di .env
uvicorn app.main:app --reload --port 8000
```
API akan berjalan di `http://127.0.0.1:8000`. Dokumentasi API interaktif (*Swagger UI*) dapat diakses di `http://127.0.0.1:8000/docs`.

### 2. Menjalankan Frontend (Vue.js)
Buka terminal baru lainnya dan arahkan ke folder `frontend`:
```bash
cd frontend
npm install
npm run dev
```
Aplikasi web (UI) akan berjalan di `http://localhost:5173`. Frontend sudah dikonfigurasi untuk otomatis mengarah ke `http://127.0.0.1:8000/api/v1` jika dijalankan di mode *development* (lokal).

## Panduan Deployment (Production)

Proyek ini telah dioptimasi sedemikian rupa agar dapat di-*deploy* seluruhnya (Frontend & Backend) ke dalam infrastruktur **Vercel** melalui konfigurasi `vercel.json` di *root directory*.

Langkah Deployment ke Vercel:
1. Hubungkan repositori GitHub ini ke proyek Vercel Anda.
2. Pastikan **Root Directory** dibiarkan kosong (`./`).
3. Vercel akan membaca `vercel.json` dan secara otomatis melakukan *build* untuk Vue.js (`frontend/dist`) serta membungkus kerangka kerja FastAPI (`api/index.py`) menjadi Vercel Serverless Functions.
4. *Environment Variables* tidak memerlukan modifikasi `VITE_API_URL` karena *routing* internal sudah dikonfigurasi untuk menggunakan alamat relatif `/api/v1`.

## Deployment Produksi (Self-hosted Docker + Nginx)

Selain Vercel, proyek ini juga bisa di-deploy ke server self-hosted yang sudah menjalankan beberapa project lain di balik satu Nginx (`planning.mge.co.id`), dengan path:

- Frontend: `planning.mge.co.id/optrack`
- API: `planning.mge.co.id/api/optrack/xxx`

Alur deploy (otomatis lewat `.github/workflows/deploy.yml` setiap push ke `main`):
1. Backend di-build jadi Docker image (`Dockerfile` di root) dan di-push ke GitHub Container Registry (GHCR).
2. Frontend di-build dengan `VITE_BASE_PATH=/optrack/` agar semua asset & routing mengarah ke sub-path yang benar.
3. Hasil build frontend dan folder `scripts/` di-copy ke server lewat SSH/SCP.
4. Container backend (`optrack-backend`) dijalankan di `127.0.0.1:8002`, kredensial diambil dari `--env-file /data/secrets/planning/optrack.env`.
5. `scripts/upsert_nginx_optrack.sh` dijalankan otomatis di server untuk menambah/replace block `location /optrack` dan `location /api/optrack` pada `planning.mge.co.id.conf`, lalu reload Nginx.

**GitHub Secrets yang wajib di-set di repo ini** sebelum workflow bisa jalan: `SERVER_HOST`, `SERVER_USERNAME`, `SSH_KEY`, `GHCR_TOKEN`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `FUEL_API_URL`, `FUEL_API_KEY`. GitHub Environment bernama `production` juga perlu dibuat di *repository settings*.

---
*Developed and Maintained by the Planning Department Team.*
