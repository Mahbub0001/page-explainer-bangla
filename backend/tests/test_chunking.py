import pytest
from app.services.chunking import chunk_text
from app.config import get_settings


def test_chunking_with_bangla_danda():
    text = (
        "এটি প্রথম বাক্য। এটি দ্বিতীয় বাক্য। এটি তৃতীয় বাক্য। "
        "এখানে অনেক কথা বলা হয়েছে। আমাদের সুন্দর বাংলাদেশ।"
    )
    docs, truncated = chunk_text(text, page_id="p1", title="Title 1")
    assert len(docs) >= 1
    assert not truncated
    assert docs[0].metadata["page_id"] == "p1"
    assert docs[0].metadata["title"] == "Title 1"
    assert docs[0].metadata["chunk_id"] == 0


def test_chunking_drops_tiny_chunks():
    # Chunks with fewer than 20 non-space characters are dropped
    text = "ok\n\nshort\n\n" + "এটি একটি বিস্তারিত বাক্য যা বিশ অক্ষরের বেশি লম্বা।"
    docs, _ = chunk_text(text, page_id="p2", title="Title 2")
    # "ok" and "short" are < 20 non-space chars, should be filtered out
    assert len(docs) == 1
    assert "বিস্তারিত বাক্য" in docs[0].page_content


def test_chunking_caps_max_chunks(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "MAX_CHUNKS", 3)
    monkeypatch.setattr(settings, "CHUNK_SIZE", 30)
    monkeypatch.setattr(settings, "CHUNK_OVERLAP", 0)

    long_text = "\n\n".join([f"এটি একটি অর্থপূর্ণ বাক্য নম্বর {i} যা বিশ অক্ষরের অধিক।" for i in range(10)])
    docs, truncated = chunk_text(long_text, page_id="p3", title="Title 3")
    assert len(docs) == 3
    assert truncated is True
