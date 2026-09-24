# Bangla Page Explainer — Backend

FastAPI + LangChain backend for Bangla Page Explainer Chrome Extension.

## Setup & Running

### 1. Prerequisites
- Python 3.11 or newer

### 2. Virtual Environment
```bash
# On macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate

# On Windows (PowerShell):
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Copy `.env.example` to `.env` and set your Google Gemini API key:
```bash
cp .env.example .env
```
Edit `.env`:
```
GOOGLE_API_KEY=your_actual_gemini_api_key
```

### 5. Run the Server
```bash
uvicorn app.main:app --reload --port 8000
```
Server runs at `http://localhost:8000`.

### 6. Run Tests
```bash
pytest -q
```
