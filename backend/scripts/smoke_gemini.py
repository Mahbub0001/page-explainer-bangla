"""Smoke test script for Gemini LLM and Embeddings.

Verifies:
1. Environment variables and API key configuration.
2. Embedding model generation for Bangla and English text.
3. Chat model invocation and response in Bangla.
"""

import os
import sys
from pathlib import Path

# Ensure UTF-8 stdout/stderr for Windows terminals
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

# Load .env
env_path = backend_dir / ".env"
load_dotenv(dotenv_path=env_path)

api_key = os.getenv("GOOGLE_API_KEY", "").strip()
if not api_key or api_key == "your-gemini-api-key-here":
    print("❌ ERROR: GOOGLE_API_KEY is not set or still has the placeholder value in backend/.env.")
    print("Please add a valid Google Gemini API key to backend/.env and re-run.")
    sys.exit(1)

chat_model = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
embedding_model = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")

print(f"Testing with Chat Model: {chat_model}")
print(f"Testing with Embedding Model: {embedding_model}")

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

def extract_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for p in content:
            if isinstance(p, str):
                parts.append(p)
            elif isinstance(p, dict) and "text" in p:
                parts.append(p["text"])
        return "".join(parts)
    return str(content)

try:
    print("\n--- 1. Testing Embeddings ---")
    embeddings = GoogleGenerativeAIEmbeddings(model=embedding_model, google_api_key=api_key)
    
    bn_vec = embeddings.embed_query("এটি একটি বাংলা বাক্য।")
    en_vec = embeddings.embed_query("This is an English test sentence.")
    
    print(f"✅ Bangla embedding vector length: {len(bn_vec)}")
    print(f"✅ English embedding vector length: {len(en_vec)}")
    
    print("\n--- 2. Testing Chat Model ---")
    llm = ChatGoogleGenerativeAI(model=chat_model, google_api_key=api_key, temperature=0.3)
    response = llm.invoke("১ লাইনে বাংলায় নিজের পরিচয় দাও")
    
    reply_text = extract_text(response.content)
    print(f"✅ Chat reply:\n{reply_text.strip()}")
    
    print("\n🎉 All Gemini smoke tests passed successfully!")
    sys.exit(0)

except Exception as e:
    print(f"\n❌ Error testing Gemini models: {e}")
    sys.exit(2)
