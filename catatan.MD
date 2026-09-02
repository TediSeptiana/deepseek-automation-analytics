# 🚀 DeepSeek Automation & Analytics FastAPI Service

## 📌 Ringkasan Proyek (Executive Summary)

Proyek ini adalah **Automation & Scraping Engine berbasis Web Service** yang memfungsikan **Playwright (Async API)** untuk mengotomatisasi interaksi dengan situs web **DeepSeek Chat**.

Layanan ini dibungkus menggunakan **FastAPI (Python 3.11+)** untuk menyediakan antarmuka RESTful API bagi klien eksternal. Sistem ini dirancang khusus untuk melewati kerumitan login berulang dengan fitur **Session Caching (Cookie Storage State)**, penanganan **CAPTCHA / Cloudflare secara fleksibel (Human Intervention Protocol)**, serta dilengkapi **Raw Data Exporter** untuk kebutuhan analisis data (NLP/Prompt Benchmarking).

---

## 🛠️ Arsitektur & Spesifikasi Teknologi

- **Bahasa Pemrograman**: Python 3.11+ (Type-safe, Idiomatic AsyncIO)
- **Framework Web**: FastAPI + Uvicorn
- **Browser Engine**: Playwright (Python Async API, Chromium, `headless=False`)
- **Data Validation & Settings**: Pydantic V2 & `python-dotenv`
- **Session Management**: Storage State (`deepseek_state.json`) untuk caching cookie/session
- **Storage & Logging**:
  - `data/state/`: Menyimpan file kredensial & cookie sesi browser.
  - `data/log/`: Operational Log dalam format teks polos (`.txt`).
  - `data/json/`: Operational Log dalam format JSON terstruktur (`.json`).
  - `data/raw/`: Dataset mentah (_Raw Input/Output Data_) untuk kebutuhan analisis data.

---

## 🏗️ Struktur Folder Proyek

```text
animation/
├── .env                        # File kredensial (DEEPSEEK_EMAIL & DEEPSEEK_PASSWORD)
├── main.py                     # Entrypoint server Uvicorn & App Lifespan Management
├── cobaocba.py                 # Client script untuk testing & integrasi API
├── app/
│   ├── config.py               # Central configuration & directory initializers
│   ├── models.py               # Schema Pydantic (Request, Response, & Analytical Models)
│   ├── services/
│   │   ├── browser_service.py  # Singleton Browser Engine (Playwright Async + CAPTCHA Manager)
│   │   └── exporter_service.py # Log & Raw Dataset Exporter
│   └── routers/
│       └── chat_router.py      # Endpoint REST API (/health, /chat)
└── data/
    ├── state/                  # State browser & cookies (JSON)
    ├── log/                    # Log teks operasional
    ├── json/                   # Log JSON operasional
    └── raw/                    # Raw dataset untuk analisis
```
