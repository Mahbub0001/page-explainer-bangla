import sys
import time
import httpx

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sample = (
    "The Solar System is the gravitationally bound system of the Sun and the objects that orbit it. "
    "It formed 4.6 billion years ago from the gravitational collapse of a giant interstellar molecular cloud. "
    "The vast majority of the system mass is in the Sun, with the majority of the remaining mass contained in the planet Jupiter. "
    "The four inner system planets—Mercury, Venus, Earth and Mars—are terrestrial planets, being composed primarily of rock and metal. "
    "The four outer planets are giant planets, being substantially larger and more massive than the terrestrials. "
) * 200

payload = {
    "url": "https://en.wikipedia.org/wiki/Solar_System",
    "title": "Solar System",
    "text": sample,
    "truncated": False,
    "lang": "en",
}

print(f"Sending {len(payload['text'])} chars to backend...")
start = time.time()
res = httpx.post("http://localhost:8000/api/v1/pages/index", json=payload, timeout=60.0)
print("Response Status:", res.status_code)
data = res.json()
print("Response Data:", data)
assert res.status_code == 200
print(f"SUCCESS! Indexed in {time.time() - start:.2f}s, chunk_count={data['chunk_count']}, truncated={data['truncated']}")
