# Bangla Page Explainer (বাংলা পেজ এক্সপ্লেইনার)

> Understand any web page in simple, natural Bangla with AI-powered RAG (Retrieval-Augmented Generation), grounded sources, and instant streaming.

Bangla Page Explainer is a Chrome Manifest V3 extension paired with a lightweight FastAPI + LangChain backend using Google's Gemini models. It allows Bangla-speaking students, professionals, and readers to summarize English articles, ask in-depth questions, or select confusing passages for easy-to-understand explanations—all answered in fluent Bangla script with cited sources from the original page.

---

## 🌟 Key Features

- **One-Click Page Analysis:** Extracts readable article text via Mozilla Readability and indexes it locally using Gemini multilingual embeddings.
- **Grounded Q&A (RAG):** Answers only from the page content with clickable citations `[1]`, `[2]`. When information is missing from the page, it refuses honestly and never hallucinates.
- **Plain Bangla Output:** Technical terms are introduced with their English names in parentheses (e.g. `নিউরাল নেটওয়ার্ক (Neural Network)`).
- **Fast Token Streaming:** Real-time token streaming via NDJSON for immediate responsiveness.
- **Explain Selection:** Select any paragraph, term, or formula on the page and get a clear, simplified explanation with real-life analogies.
- **Privacy & Safety First:** Pages are analyzed strictly on demand; in-memory vector storage with automatic 2-hour TTL expiration. Resistant to prompt injection attacks.
- **No-Build Extension:** Vanilla JavaScript with ES modules, zero compilation, and lightweight styling supporting both light and dark modes.

---

## 📂 Project Structure

```
bangla-page-explainer/
├── README.md
├── .gitignore
├── docs/
│   ├── PRD.md                 # Product Requirements Document
│   ├── TRD.md                 # Technical Requirements Document
│   ├── Phases.md              # Build & implementation plan
│   ├── DECISIONS.md           # Engineering & architectural decision log
│   └── EVAL.md                # Security, grounding, and accuracy evaluation
├── backend/
│   ├── requirements.txt       # Pinned backend dependencies
│   ├── .env.example           # Environment template
│   ├── pytest.ini             # Test configuration
│   ├── app/
│   │   ├── main.py            # FastAPI factory, middleware, exception handlers
│   │   ├── config.py          # Pydantic settings
│   │   ├── schemas.py         # Request & response validation models
│   │   ├── errors.py          # Unified error handlers & standard error JSON
│   │   ├── logging_setup.py   # Safe structured logger
│   │   ├── ratelimit.py       # Rolling window IP rate limiter
│   │   ├── routers/
│   │   │   ├── health.py      # GET /health
│   │   │   ├── pages.py       # POST /api/v1/pages/index
│   │   │   └── ai.py          # POST summarize / chat / explain-selection
│   │   └── services/
│   │       ├── models.py      # LLM and Embedding factories
│   │       ├── chunking.py    # Recursive chunking with Bangla danda delimiter
│   │       ├── page_store.py  # In-memory LRU + TTL vector store manager
│   │       ├── prompts.py     # System and task prompt templates
│   │       ├── rag.py         # Query rewriting, retrieval & chat streaming
│   │       ├── summarize.py   # Stuff & map-reduce page summarizer
│   │       └── streaming.py   # NDJSON chunk normalization & streaming helpers
│   ├── scripts/
│   │   ├── smoke_gemini.py    # API key and model connectivity verification
│   │   └── generate_icons.py  # PNG icon generator for Chrome extension
│   └── tests/
│       ├── conftest.py        # Deterministic fake LLM & fake embedding fixtures
│       ├── test_health.py     # Health and schema validation tests
│       ├── test_chunking.py   # Separator, overlap, and chunk filtering tests
│       ├── test_pages.py      # Page indexing & cache tests
│       ├── test_chat.py       # RAG chat streaming, history, and fallback tests
│       ├── test_summarize.py  # Stuff vs. map-reduce and explain selection tests
│       ├── test_errors_limits.py # Error mapping & rate limiting tests
│       └── eval/
│           ├── injection.html # Adversarial prompt-injection test page
│           └── questions.md   # 10 pages x 5 questions evaluation suite
└── extension/
    ├── manifest.json          # Chrome Manifest V3 configuration
    ├── background.js          # Service worker for side panel opening
    ├── icons/                 # 16, 32, 48, 128 px PNG icons
    ├── lib/
    │   └── Readability.js     # Vendored Mozilla Readability library
    ├── content/
    │   └── extract.js         # DOM content extractor, login guard, and highlighter
    └── sidepanel/
        ├── sidepanel.html     # Side panel interface layout
        ├── sidepanel.css      # Typography, light/dark themes, responsive UI
        ├── sidepanel.js       # UI controller, event handlers, streaming integration
        ├── state.js           # Multi-tab session state management
        ├── api.js             # NDJSON stream consumer and API client
        ├── page.js            # Scripting injection and page interaction helpers
        ├── render.js          # Safe XSS-proof DOM renderer with markdown subset
        ├── i18n.js            # Complete Bangla/English localization dictionary
        └── settings.js        # Persistent settings in chrome.storage.local
```

---

## 🚀 Quick Start (Under 10 Minutes)

### Step 1: Clone & Prerequisites
- Python 3.11+
- Google Chrome 114+ (supports Side Panel API)
- A free Google Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### Step 2: Backend Setup

#### On Windows (PowerShell):
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### On macOS / Linux:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and set your Gemini API key:
```ini
GOOGLE_API_KEY=AIzaSy...your_gemini_key_here
```

Verify your setup with the smoke test script:
```bash
python scripts/smoke_gemini.py
```

### Step 4: Run the Backend Server
```bash
uvicorn app.main:app --reload --port 8000
```
The server will start at `http://localhost:8000`. You can verify health by opening `http://localhost:8000/health` in your browser.

### Step 5: Install the Chrome Extension
1. Open Google Chrome and go to `chrome://extensions/`.
2. Toggle **Developer mode** on (top right switch).
3. Click **Load unpacked** (top left button).
4. Select the `extension/` folder from this repository.
5. Pin the **Bangla Page Explainer** icon to your Chrome toolbar.

---

## 📖 How to Use

1. **Browse:** Open any article, documentation page, or news site in English or Bangla.
2. **Open Explainer:** Click the extension icon in the toolbar. The side panel opens on the right.
3. **Analyze:** Click **"এই পেজ বিশ্লেষণ করুন"** (Analyze this page). In a few seconds, the page is indexed.
4. **Summarize:** Click **"সারসংক্ষেপ"** (Summary) to get an overview and key takeaways in Bangla.
5. **Ask Doubts:** Type any question in Bangla, English, or romanized Bangla (`eta ki niye lekha?`) and press Enter.
6. **Explain Passages:** Highlight text on the webpage, then click **"নির্বাচিত অংশ বুঝিয়ে দিন"** in the side panel.
7. **Jump to Source:** Click any source citation chip `[1]` or **"পেজে দেখুন"** to jump and highlight the exact text on the webpage.

---

## 🔒 Security & Privacy

- **On-Demand Reading:** The extension **never** reads any webpage automatically in the background. It reads text only when you explicitly click "এই পেজ বিশ্লেষণ করুন".
- **Sensitive Page Protection:** Automatically blocks login/password pages and privileged browser pages (`chrome://`, PDF viewer, Chrome Web Store).
- **In-Memory Storage:** The backend keeps index data in volatile RAM only. No page text is written to disk or permanent databases. Indexed pages automatically expire after 2 hours (TTL) or via LRU cache.
- **XSS & Injection Protection:** The extension UI uses pure DOM element creation (`document.createElement`, `textContent`) without `innerHTML` for dynamic content.
- **Adversarial Resilience:** The prompt treats page context as strictly untrusted data, preventing prompt injection attacks from hijacking answers.
- **Data Sharing Disclosure:** Extracted page content and questions are transmitted via your local backend to Google's Gemini API endpoints. When using free-tier API keys, Google's standard terms of service apply.

---

## 🧪 Testing

Run the automated test suite with pytest:
```bash
cd backend
pytest -q
```
All 23 unit tests run deterministically offline using simulated embedding and chat models.

---

## 🛠️ Troubleshooting

| Problem | Cause | Solution |
|---|---|---|
| **"সার্ভারের সাথে সংযোগ হচ্ছে না"** | Backend server is not running | Start backend using `uvicorn app.main:app --port 8000`. |
| **"এই পেজ পড়া সম্ভব নয়"** | Browser internal page or PDF | Chrome restricts extensions from injecting into `chrome://` URLs, Web Store, and PDF viewer. |
| **"এটি লগইন পেজ মনে হচ্ছে"** | Page contains visible password fields | By design, sensitive login pages are guarded against extraction. |
| **"AI-এর ব্যবহারের সীমা শেষ"** | Free-tier Gemini quota hit | Wait a minute before retrying, or check quota limits in Google AI Studio. |
| **Windows PowerShell script activation error** | Execution policy restriction | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then activate venv. |
| **Port 8000 already in use** | Another process on 8000 | Specify a different port: `uvicorn app.main:app --port 8080`, and update Backend URL in extension Settings. |

---

## 📄 License
This project is open-source under the MIT License. Mozilla Readability is licensed under the Apache 2.0 License.
