# docgen v1

Generator dokumentasi Python yang membaca source dengan `ast`, membangun context,
mengirim prompt ke local LLM melalui `aiohttp`, lalu menyimpan hasil sebagai Markdown.

## Requirement

- Python 3.11+
- Local API:
  - `GET /api/v1/health`
  - `POST /api/v1/chat`
- `/chat` mengembalikan JSON dengan field string `response`.

## Install

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

Linux/macOS:
```bash
source .venv/bin/activate
```

```bash
python -m pip install -e .
```

## Run

```bash
docgen ./examples/calculator.py --output ./docs
```

Directory:
```bash
docgen ./my_project/src --output ./docs
```

Custom endpoint:
```bash
docgen ./my_project/src --output ./docs --base-url http://127.0.0.1:8000/api/v1
```

Tanpa install sebagai package:
```bash
python -m docgen.cli ./examples/calculator.py --output ./docs
```
