
from services.vector_store import chunk_text


def test_long_paper_creates_multiple_chunks():
    text = "Scientific research data. " * 150

    chunks = chunk_text(text)

    assert len(chunks) > 1
    assert all(len(chunk) <= 1000 for chunk in chunks)


def test_chunk_overlap():
    text = "".join(str(i % 10) for i in range(2000))

    chunks = chunk_text(text)

    assert chunks[0][-150:] == chunks[1][:150]


def test_empty_paper_rejected():
    try:
        chunk_text("")
    except ValueError:
        return

    raise AssertionError("Empty paper should raise ValueError")
