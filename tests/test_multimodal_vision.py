"""Unit and integration tests for Multimodal Vision Service (Week 3, Member 3).

Tests:
1. Figure extraction from research PDFs using PyMuPDF.
2. Filtering of small artifact icons/banners.
3. Provenance tracking: figure_id, page_number, dimensions.
4. Gemini Vision structured analysis parsing and fallback behavior.
5. Error handling for empty or invalid PDF input.
"""

from unittest.mock import patch, MagicMock
import pytest

from services.multimodal_vision import (
    extract_figures_from_pdf,
    analyze_scientific_figure,
    _parse_vision_response,
    _fallback_visual_analysis,
)


def _create_sample_pdf_with_image(width=200, height=200) -> bytes:
    """Helper to generate a minimal in-memory PDF with an embedded image."""
    import fitz
    from PIL import Image
    import io

    # Create dummy PIL image
    img = Image.new("RGB", (width, height), color=(73, 109, 137))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    rect = fitz.Rect(50, 50, 50 + width, 50 + height)
    page.insert_image(rect, stream=img_bytes)

    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def test_extract_figures_from_pdf_success():
    """Verify that legitimate figures are extracted with metadata and image bytes."""
    pdf_bytes = _create_sample_pdf_with_image(width=300, height=250)
    figures = extract_figures_from_pdf(pdf_bytes, paper_id="arxiv:2610.1234", max_figures=5)

    assert len(figures) == 1
    fig = figures[0]
    assert fig["paper_id"] == "arxiv:2610.1234"
    assert fig["page_number"] == 1
    assert fig["width"] == 300
    assert fig["height"] == 250
    assert fig["image_ext"] == "png"
    assert len(fig["image_bytes"]) > 0
    assert "Figure 1 (Page 1)" in fig["reference_label"]


def test_extract_figures_filters_small_icon_artifacts():
    """Verify that images smaller than MIN_FIGURE_WIDTH/HEIGHT are filtered out."""
    pdf_bytes = _create_sample_pdf_with_image(width=50, height=50)  # Tiny icon artifact
    figures = extract_figures_from_pdf(pdf_bytes, paper_id="pubmed:12345")

    assert len(figures) == 0


def test_extract_figures_invalid_input_raises():
    """Verify invalid or empty input raises ValueError."""
    with pytest.raises(ValueError, match="pdf_bytes must be non-empty bytes"):
        extract_figures_from_pdf(b"")


def test_analyze_scientific_figure_fallback():
    """Verify fallback response when GEMINI_API_KEY is absent."""
    with patch.dict("os.environ", {}, clear=True):
        res = analyze_scientific_figure(
            image_bytes=b"dummy_bytes",
            figure_label="Figure 2",
            paper_title="CRISPR Analysis",
            research_topic="Gene Editing",
        )

    assert res["status"] == "fallback"
    assert res["figure_label"] == "Figure 2"
    assert "placeholder" in res["analysis"]
    assert len(res["limitations"]) >= 1


def test_analyze_scientific_figure_gemini_vision_success():
    """Verify live/mocked Gemini Vision response parsing."""
    mock_response = MagicMock()
    mock_response.text = (
        "FIGURE_TYPE: Bar Plot\n"
        "AXES_AND_LABELS: X-axis represents cell types; Y-axis represents editing efficiency (%)\n"
        "VISUAL_FINDINGS: HF1 variant achieves 88% efficiency in HEK293T, outperforming wildtype.\n"
        "METHODOLOGICAL_LIMITATIONS: Error bars indicate standard deviation across n=3 biological replicates."
    )

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with (
        patch.dict("os.environ", {"GEMINI_API_KEY": "fake-key"}),
        patch("google.genai.Client", return_value=mock_client),
    ):
        res = analyze_scientific_figure(
            image_bytes=b"fake_image_bytes",
            figure_label="Figure 1 (Page 2)",
            paper_title="High-fidelity Cas9 Variants",
            research_topic="Gene Editing Specificity",
        )

    assert res["status"] == "success"
    assert res["figure_type"] == "Bar Plot"
    assert "88% efficiency" in res["analysis"]
    assert len(res["limitations"]) >= 1


def test_parse_vision_response_defaults():
    raw_text = "General diagram showing experimental setup without explicit figure type tag."
    parsed = _parse_vision_response(raw_text, "Fig 3")
    assert parsed["figure_type"] == "Scientific Diagram / Chart"
    assert parsed["figure_label"] == "Fig 3"
