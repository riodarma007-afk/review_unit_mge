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
3. Akses ke koneksi database MySQL utama yang didefinisikan dalam `.env` atau konfigurasi `backend/app/core/config.py`.

## Cara Menjalankan Secara Lokal (Development)

Proyek ini dapat dijalankan di perangkat lokal untuk kebutuhan *development* dan pengetesan.

### 1. Menjalankan Backend (FastAPI)
Buka terminal baru dan arahkan ke folder `backend`:
```bash
cd backend
pip install -r requirements.txt
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

---
*Developed and Maintained by the Planning Department Team.*
