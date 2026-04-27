# MAL Document Intelligence System

Upload PDFs or images (or pull files from optional **IBM BPM** and **FileNet** HTTP endpoints), extract text, and ask questions in natural language. Connection pools are configured from the **Connections** tab in the web UI (saved under `backend/data/`, gitignored). Answers use your document text (Arabic and English supported).

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** (for the web UI)
- **Groq API key** (free tier at [Groq Console](https://console.groq.com/)) — required for Q&A

Windows, macOS, and Linux are supported.

## Quick start

### 1. Clone and create a virtual environment

```bash
cd /path/to/arabic-vision-poc
python -m venv venv
```

**Windows**

```bat
venv\Scripts\activate
```

**macOS / Linux**

```bash
source venv/bin/activate
```

### 2. Install backend dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure environment

Copy the example env file and add your Groq key:

- **Windows:** `copy .env.example .env`
- **macOS / Linux:** `cp .env.example .env`

Edit **`.env`** in the project root and set at least:

```env
GROQ_API_KEY=your_key_here
```

Optional: `GROQ_MODEL` (default `llama-3.1-8b-instant`), `OCR_LANGUAGE` (e.g. `ar,en`).

### 4. Install and run the frontend

```bash
cd frontend
npm install
npm run dev
```

Leave this terminal open. The UI is at **http://localhost:3000** (Vite default port).

### 5. Run the API

Open a **second** terminal, activate the same `venv`, then:

```bash
cd backend
python app.py
```

The API listens on **http://localhost:8000** (`GET /health` to verify).

### One-command option (Windows)

From the repo root, after `venv` exists and dependencies are installed:

```bat
run.bat
```

This frees ports **8000** and **3000**, starts the backend, then starts the frontend.

---

## Optional: IBM BPM and FileNet (connection pools)

### Configure in the web UI

1. Open the app and go to **Connections**.
2. Enter **base URL**, **pool connections**, **pool max size**, **HTTP timeout**, and optional **Basic** or **Bearer** credentials for IBM BPM and/or FileNet.
3. Click **Save & apply pools**. The API writes `backend/data/integration_settings.json` (ignored by git) and rebuilds the pooled HTTP clients immediately.

If no UI file exists yet, values from **`.env`** (`BPM_*` / `FILENET_*`) are used as defaults.

Password and bearer fields: leave blank to keep existing stored values; type a new value to replace. The API uses the sentinel `__KEEP__` internally for “unchanged”.

### Optional `.env` defaults (same names as before)

| Variable | Meaning |
|----------|--------|
| `BPM_BASE_URL` | Default BPM root URL if not overridden by the UI file |
| `BPM_POOL_CONNECTIONS` / `BPM_POOL_MAXSIZE` / `BPM_HTTP_TIMEOUT_SEC` | Pool and timeout defaults |
| `BPM_USERNAME` / `BPM_PASSWORD` / `BPM_BEARER_TOKEN` | Optional auth defaults |

Same pattern for FileNet with the `FILENET_*` prefix.

**Security:** `resource_url` on import must use the **same host and port** (`netloc`) as the configured base URL (reduces accidental SSRF).

### API

- `GET /integrations/settings` — form values + active pool summary  
- `PUT /integrations/settings` — save body `{ "ibm_bpm": { ... }, "filenet": { ... } }` (same shape as `GET` → `form`, with `password` / `bearer_token` set to `__KEEP__` when unchanged)
- `POST /integrations/bpm/document` — JSON: `{ "filename": "case.pdf", "relative_path": "path/under/base" }` **or** `{ "filename": "case.pdf", "resource_url": "https://same-host/..." }`
- `POST /integrations/filenet/document` — same body shape as BPM import

Response matches `POST /upload`. Text extraction runs in the background as usual.

`GET /health` includes integration flags and `ibm_bpm_pool` / `filenet_pool` runtime summaries when pools are active.

---

## Project layout

- `backend/` — FastAPI app (`app.py`), text extraction, Q&A, `connectors/` for BPM/FileNet pools, `data/integration_settings.json` (UI-saved connectors)
- `frontend/` — React + Vite UI
- `.env` — local secrets (not committed)

## Troubleshooting

- **503 on `/ask` or upload** — Backend not running or `GROQ_API_KEY` missing in `.env`.
- **Port already in use** — Stop other apps on ports 8000 / 3000 or change `API_PORT` / Vite port in `frontend/vite.config.ts`.
- **Blank UI** — Ensure `npm run dev` is running and open **http://localhost:3000**.

# mal-di
