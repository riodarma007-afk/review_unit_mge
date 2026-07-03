# OPTRACK Dashboard

Sistem dashboard berbasis web modern untuk memantau performa unit hauling dan overburden (OB) secara real-time.

## Teknologi
- **Backend**: FastAPI (Python), SQLAlchemy, Pandas, Pydantic
- **Frontend**: Vue.js 3 (Vite), Pinia, Axios, Vue-ApexCharts
- **Database**: MySQL

## Persyaratan
- Python 3.10+
- Node.js 18+

## Cara Menjalankan Aplikasi

### 1. Backend (FastAPI)
Buka terminal dan navigasi ke direktori `backend/`:
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

Buat file `.env` di dalam folder `backend/` berdasarkan `backend/.env.example` (atau konfigurasi yang telah disediakan `app/core/config.py`).

Jalankan server:
```bash
uvicorn app.main:app --reload
```
API akan berjalan di `http://127.0.0.1:8000`. 
Dokumentasi Swagger tersedia di `http://127.0.0.1:8000/docs`.

### 2. Frontend (Vue 3)
Buka terminal baru dan navigasi ke direktori `frontend/`:
```bash
cd frontend
npm install
npm run dev
```
Dashboard akan berjalan di `http://localhost:5173`.
