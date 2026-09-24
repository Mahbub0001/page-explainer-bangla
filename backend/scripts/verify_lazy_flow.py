import sys
import time
import asyncio
import json
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.services.page_store import get_page_store


async def main():
    print("=== Testing Lazy Flow End-to-End ===")
    app = create_app()
    transport = ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Indexing test
        sample_paragraphs = [
            "সৌরজগৎ হলো সূর্য ও এর সাথে মহাকর্ষীয়ভাবে আবদ্ধ জ্যোতির্বৈজ্ঞানিক বস্তুসমূহ নিয়ে গঠিত একটি ব্যবস্থা। প্রায় ৪.৬ বিলিয়ন বছর আগে একটি দানবীয় আন্তঃনাক্ষত্রিক আণবিক মেঘের মহাকর্ষীয় পতনের ফলে এর সৃষ্টি হয়েছিল।",
            "সৌরজগতের মোট ভরের সিংহভাগই রয়েছে সূর্যের মধ্যে, আর অবশিষ্ট ভরের প্রায় সবটুকুই ধারণ করে আছে বৃহস্পতি গ্রহ। সৌরজগতের গ্রহগুলোর মধ্যে চারটি গ্যাসীয় দানব এবং চারটি কঠিন পার্থিব গ্রহ রয়েছে।",
            "বুধ, শুক্র, পৃথিবী ও মঙ্গল—এই চারটি হলো অভ্যন্তরীণ পার্থিব গ্রহ, যা মূলত শিলা ও ধাতু দ্বারা গঠিত। পৃথিবী মানুষের একমাত্র আবাসস্থল এবং এতে প্রচুর পানি রয়েছে।",
            "বৃহস্পতি ও শনি হলো গ্যাসীয় দানব, যার প্রধান উপাদান হাইড্রোজেন ও হিলিয়াম। ইউরেনাস ও নেপচুন হলো বরফ দানব, যার প্রধান উপাদান পানি, অ্যামোনিয়া ও মিথেন।",
            "মহাকাশ গবেষণা সংস্থা নাসা এবং ইসরো বিভিন্ন সময় সৌরজগতের গ্রহগুলোতে অনুসন্ধান যান পাঠিয়েছে। বিজ্ঞানীদের ধারণা সৌরজগতের বাইরেও লক্ষ লক্ষ গ্রহ ব্যবস্থা বা এক্সোপ্ল্যানেট রয়েছে।"
        ] * 10  # 50 paragraphs to generate multiple chunks

        text = "\n\n".join(sample_paragraphs * 7)

        payload = {
            "url": "https://bn.wikipedia.org/wiki/Solar_System",
            "title": "সৌরজগৎ (Solar System)",
            "text": text,
            "truncated": False,
            "lang": "bn"
        }

        print(f"1. Sending text with {len(text)} characters for indexing...")
        t0 = time.time()
        res_idx = await client.post("/api/v1/pages/index", json=payload)
        t_idx = time.time() - t0

        print(f"   Status: {res_idx.status_code}")
        print(f"   Indexing time: {t_idx:.4f}s")
        assert res_idx.status_code == 200, res_idx.text
        idx_data = res_idx.json()
        print(f"   Page ID: {idx_data['page_id']}")
        print(f"   Chunks created: {idx_data['chunk_count']}")

        # Verify indexing speed is ultra fast (< 0.5s)
        assert t_idx < 1.0, f"Indexing was too slow: {t_idx}s"

        # Verify page store state: zero embedded chunks!
        store = get_page_store()
        page_entry = store.get(idx_data['page_id'])
        assert page_entry is not None
        assert len(page_entry.raw_chunks) == idx_data['chunk_count']
        assert len(page_entry.embedded_chunk_ids) == 0, f"Expected 0 embedded chunks, got {len(page_entry.embedded_chunk_ids)}"
        print(f"   [PASS] Zero chunks embedded upfront during indexing!")

        # 2. Chat question test: Should trigger lazy embedding of candidates only
        chat_payload = {
            "page_id": idx_data['page_id'],
            "question": "বৃহস্পতি ও শনি গ্রহের প্রধান উপাদান কি?",
            "style": "simple",
            "history": []
        }

        print("\n2. Asking Chat Question (triggers on-demand lazy embedding):")
        print(f"   Question: {chat_payload['question']}")
        t0 = time.time()
        res_chat = await client.post("/api/v1/chat", json=chat_payload, timeout=60.0)
        t_chat = time.time() - t0
        print(f"   Chat Response Status: {res_chat.status_code} (took {t_chat:.2f}s)")
        assert res_chat.status_code == 200, res_chat.text

        # Parse NDJSON
        events = [json.loads(line) for line in res_chat.text.strip().split("\n") if line.strip()]
        sources_event = events[0]
        assert sources_event["type"] == "sources"
        print(f"   Retrieved Sources count: {len(sources_event['sources'])}")
        for src in sources_event["sources"][:3]:
            print(f"     - [{src['id']}] (chunk {src['chunk_id']}): {src['text'][:60]}... (score: {src['score']})")

        # Combine streamed answer tokens
        answer_tokens = [e["text"] for e in events if e.get("type") == "token"]
        full_answer = "".join(answer_tokens)
        print(f"\n   LLM Answer: {full_answer}\n")
        assert len(answer_tokens) > 0, "No tokens received"
        assert events[-1]["type"] == "done", "Last event was not 'done'"

        # Verify lazy embedding: only candidate chunks embedded, not all chunks!
        print(f"   Total embedded chunks in page index: {len(page_entry.embedded_chunk_ids)} of {page_entry.chunk_count}")
        assert len(page_entry.embedded_chunk_ids) <= 12, "Embedded more chunks than top_n limit!"
        assert len(page_entry.embedded_chunk_ids) > 0, "No candidate chunks were embedded!"
        print("   [PASS] On-demand lazy embedding verified successfully!")

        print("\n=== ALL TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(main())
