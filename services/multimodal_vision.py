"""Multimodal Vision Service for Scientific Discovery (Week 3, Member 3).

Provides end-to-end functionality to:
1. Extract images, figures, charts, and diagrams from scientific research PDFs using PyMuPDF.
2. Filter out non-figure artifacts (tiny icons, spacer bars, decorative lines).
3. Connect with Google Gemini Vision API to analyze extracted charts/figures for:
   - Chart/Figure type classification (line chart, bar plot, heatmap, gel electrophoresis, flow diagram).
   - Key visual trends, numeric labels, axes, and takeaways.
   - Traceable link to source paper ID, page number, and figure reference.
"""

from __future__ import annotations

import io
import logging
import os
import re
from typing import Any

from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

# Minimum dimensions to qualify as a scientific figure / chart
MIN_FIGURE_WIDTH = 120
MIN_FIGURE_HEIGHT = 120
MAX_FIGURES_PER_PAGE = 5


def extract_figures_from_pdf(
    pdf_bytes: bytes,
    paper_id: str = "unknown",
    max_figures: int = 10,
) -> list[dict[str, Any]]:
    """Extract embedded figures and charts from a scientific PDF.

    Args:
        pdf_bytes: Raw bytes of the research paper PDF.
        paper_id: Provenance identifier of the paper.
        max_figures: Maximum total figures to extract.

    Returns:
        List of figure dictionaries with image bytes, dimensions, and provenance metadata.
    """
    if not isinstance(pdf_bytes, bytes) or len(pdf_bytes) == 0:
        raise ValueError("pdf_bytes must be non-empty bytes.")

    import fitz  # PyMuPDF

    figures: list[dict[str, Any]] = []

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        logger.warning(f"Failed to open PDF stream for {paper_id}: {exc}")
        return []

    fig_idx = 1
    for page_idx in range(len(doc)):
        if len(figures) >= max_figures:
            break

        page = doc[page_idx]
        image_list = page.get_images(full=True)
        page_figures_count = 0

        for img_info in image_list:
            if len(figures) >= max_figures or page_figures_count >= MAX_FIGURES_PER_PAGE:
                break

            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
            except Exception as exc:
                logger.debug(f"Could not extract image xref {xref}: {exc}")
                continue

            image_bytes = base_image.get("image")
            image_ext = base_image.get("ext", "png").lower()
            width = base_image.get("width", 0)
            height = base_image.get("height", 0)

            # Filter out tiny icon artifacts and decorative banners
            if width < MIN_FIGURE_WIDTH or height < MIN_FIGURE_HEIGHT:
                continue

            figure_meta = {
                "figure_id": f"{paper_id}_fig_{fig_idx}",
                "paper_id": paper_id,
                "page_number": page_idx + 1,
                "width": width,
                "height": height,
                "image_ext": image_ext,
                "image_bytes": image_bytes,
                "reference_label": f"Figure {fig_idx} (Page {page_idx + 1})",
            }
            figures.append(figure_meta)
            fig_idx += 1
            page_figures_count += 1

    doc.close()
    return figures


def analyze_scientific_figure(
    image_bytes: bytes,
    figure_label: str = "Figure",
    paper_title: str = "",
    research_topic: str = "",
) -> dict[str, Any]:
    """Analyze a scientific chart or diagram using Google Gemini Vision.

    Args:
        image_bytes: Raw bytes of the figure image.
        figure_label: Reference label (e.g. 'Figure 1 (Page 3)').
        paper_title: Title of source paper for context.
        research_topic: Research domain or topic query.

    Returns:
        Structured analysis containing figure_type, detected_trends, visual_findings, and relevance.
    """
    if not isinstance(image_bytes, bytes) or len(image_bytes) == 0:
        raise ValueError("image_bytes must be non-empty bytes.")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # Graceful fallback when API key is not configured in environment
        return _fallback_visual_analysis(figure_label, reason="GEMINI_API_KEY is not configured.")

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

        prompt = (
            f"You are a multimodal scientific research assistant.\n"
            f"Analyze this scientific figure ({figure_label}) extracted from research paper: '{paper_title}'.\n"
            f"Research topic: '{research_topic}'.\n\n"
            f"Provide a structured analysis with:\n"
            f"1. FIGURE_TYPE: (e.g. Bar Plot, Line Graph, Heatmap, Molecular Structure, Flow Diagram, Gel Electrophoresis)\n"
            f"2. AXES_AND_LABELS: Key variables, measurements, and legends identified.\n"
            f"3. VISUAL_FINDINGS: Observed quantitative trends, effect directions, and significant data points.\n"
            f"4. METHODOLOGICAL_LIMITATIONS: Missing error bars, unclear scales, or visual ambiguities if any."
        )

        response = client.models.generate_content(
            model=model,
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/png",
                ),
                prompt,
            ],
        )

        raw_text = response.text or ""
        return _parse_vision_response(raw_text, figure_label)

    except Exception as exc:
        logger.warning(f"Gemini Vision call failed for {figure_label}: {exc}")
        return _fallback_visual_analysis(figure_label, reason=str(exc))


def _parse_vision_response(raw_text: str, figure_label: str) -> dict[str, Any]:
    """Parse Gemini Vision structured text output into a clean dictionary."""
    figure_type = "Scientific Diagram / Chart"
    match = re.search(r"FIGURE_TYPE:\s*(.+)", raw_text, re.IGNORECASE)
    if match:
        figure_type = match.group(1).strip()

    return {
        "status": "success",
        "figure_label": figure_label,
        "figure_type": figure_type,
        "analysis": raw_text.strip(),
        "limitations": [
            "Visual interpretation is model-inferred and subject to image resolution limitations."
        ],
    }


def _fallback_visual_analysis(figure_label: str, reason: str = "") -> dict[str, Any]:
    """Deterministic fallback for tests or when Vision API is unreachable."""
    return {
        "status": "fallback",
        "figure_label": figure_label,
        "figure_type": "Scientific Chart / Figure",
        "analysis": f"Figure visual analysis placeholder ({figure_label}). Reason: {reason}",
        "limitations": ["Live vision call deferred or unconfigured."],
    }
