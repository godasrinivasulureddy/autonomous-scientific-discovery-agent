import pytest

from services.vector_store import chunk_text


def test_long_paper_creates_multiple_chunks():
    text = "Scientific research data. " * 150

    chunks = chunk_text(text)

    assert len(chunks) > 1
    assert all(len(chunk) <= 1000 for chunk in chunks)
    assert "".join(chunks) != ""


def test_chunk_overlap():
    text = "".join(str(i % 10) for i in range(2000))

    chunks = chunk_text(text)

    assert len(chunks) > 1
    assert chunks[0][-150:] == chunks[1][:150]


def test_empty_paper_rejected():
    with pytest.raises(ValueError, match="Paper text cannot be empty"):
        chunk_text("")


@pytest.mark.parametrize(
    ("chunk_size", "overlap"),
    [
        (0, 0),
        (-1, 0),
        (100, -1),
        (100, 100),
        (100, 101),
        (1.5, 0),
        (100, 1.5),
        (True, 0),
        (100, False),
    ],
)
def test_invalid_chunk_settings_rejected(chunk_size, overlap):
    with pytest.raises(ValueError, match="Invalid chunk size or overlap"):
        chunk_text(
            "Sample scientific research text.",
            chunk_size=chunk_size,
            overlap=overlap,
        )


@pytest.mark.parametrize("text", [None, 123, "   "])
def test_invalid_paper_text_rejected(text):
    with pytest.raises(ValueError, match="Paper text cannot be empty"):
        chunk_text(text)


def test_chunks_reconstruct_original_text_without_overlap():
    text = "Scientific discovery evidence. " * 80

    chunks = chunk_text(text, chunk_size=100, overlap=0)

    assert "".join(chunks) == text


def test_chunk_boundaries_preserve_all_characters():
    text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 100

    chunks = chunk_text(text, chunk_size=100, overlap=20)

    assert chunks[0][:100] == text[:100]
    assert chunks[1][:80] == text[80:160]
    assert chunks[-1][-1] == text[-1]
