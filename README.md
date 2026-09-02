# DeepSeek Automation & Analytics FastAPI Service

Automation and analytics service berbasis **FastAPI** dan **Playwright Async API** untuk mengotomatisasi interaksi dengan antarmuka web DeepSeek Chat.

Project ini menyediakan REST API untuk mengelola browser session, mengirim prompt, serta menyimpan operational log dan raw input/output untuk kebutuhan analisis seperti **NLP, prompt benchmarking, dan eksperimen automation**.

> **Status:** Experimental / Personal Project

## Features

* REST API menggunakan FastAPI
* Asynchronous browser automation menggunakan Playwright
* Chromium browser management
* Session persistence menggunakan Playwright Storage State
* Human intervention untuk authentication atau browser challenge
* Operational logging
* Structured JSON logging
* Raw input/output data export
* Pydantic request/response validation
* AsyncIO-based architecture

## Technology Stack

| Component                 | Technology               |
| ------------------------- | ------------------------ |
| Language                  | Python 3.11+             |
| API Framework             | FastAPI                  |
| ASGI Server               | Uvicorn                  |
| Browser Automation        | Playwright               |
| Browser                   | Chromium                 |
| Validation                | Pydantic V2              |
| Environment Configuration | python-dotenv            |
| Async Runtime             | asyncio                  |
| Session Management        | Playwright Storage State |

## Project Structure

```text
deepseek-automation-analytics/
│
├── .gitignore
├── requirements.txt
├── main.py
├── cobaocba.py
│
├── app/
│   ├── config.py
│   ├── models.py
│   │
│   ├── services/
│   │   ├── browser_service.py
│   │   └── exporter_service.py
│   │
│   └── routers/
│       └── chat_router.py
│
└── data/
    ├── state/
    ├── log/
    ├── json/
    └── raw/
```

## Installation

Clone repository:

```bash
git clone https://github.com/<username>/deepseek-automation-analytics.git
cd deepseek-automation-analytics
```

Create virtual environment:

```bash
python -m venv .venv
```

### Windows PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install Chromium untuk Playwright:

```bash
playwright install chromium
```

## Environment Configuration

Buat file `.env` di root project:

```env
DEEPSEEK_EMAIL=your_email@example.com
DEEPSEEK_PASSWORD=your_password
```

Jangan commit `.env` ke repository.

## Session Management

Project menggunakan **Playwright Storage State** untuk mempertahankan browser session.

Session data disimpan pada:

```text
data/state/
```

Storage State dapat berisi authentication cookies dan informasi session.

Karena itu, directory berikut harus masuk `.gitignore`:

```gitignore
.env
.venv/
__pycache__/

data/state/
data/log/
data/json/
data/raw/
```

## Running the Application

Jalankan FastAPI menggunakan Uvicorn:

```bash
uvicorn main:app --reload
```

Server berjalan pada:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

Alternative documentation:

```text
http://127.0.0.1:8000/redoc
```

## API

### Health Check

```http
GET /health
```

Digunakan untuk memeriksa status service.

### Chat

```http
POST /chat
```

Contoh request:

```json
{
    "message": "Hello, DeepSeek"
}
```

Payload dapat disesuaikan dengan schema pada `app/models.py`.

## Architecture

```text
API Client
    │
    ▼
FastAPI
    │
    ▼
Chat Router
    │
    ▼
Browser Service
    │
    ▼
Playwright
    │
    ▼
Chromium
    │
    ▼
DeepSeek Web
    │
    ▼
Exporter Service
    │
    ├── Operational Logs
    ├── Structured JSON
    └── Raw Data
```

## Data Export

### Operational Logs

```text
data/log/
```

Menyimpan operational log dalam format text.

### Structured Logs

```text
data/json/
```

Menyimpan operational log dalam format JSON.

### Raw Data

```text
data/raw/
```

Digunakan untuk menyimpan raw input/output yang dapat digunakan untuk:

* NLP
* Prompt benchmarking
* Response analysis
* Dataset preparation
* Model evaluation

## Security

Project ini menggunakan browser session untuk berinteraksi dengan layanan web.

Jangan commit file atau directory berikut:

```text
.env
data/state/
data/log/
data/json/
data/raw/
```

Terutama browser Storage State karena dapat mengandung authentication cookies atau session information.

Jika credential atau session data pernah ter-upload ke repository, segera invalidate session atau credential tersebut.

## Disclaimer

Project ini dibuat untuk tujuan **learning, research, automation experimentation, dan data analysis**.

Penggunaan automation terhadap layanan pihak ketiga harus mengikuti Terms of Service dan kebijakan yang berlaku pada layanan tersebut.

Project ini tidak ditujukan untuk mengeksploitasi atau menghindari sistem keamanan layanan pihak ketiga.

## License

This project is licensed under the **MIT License**.
