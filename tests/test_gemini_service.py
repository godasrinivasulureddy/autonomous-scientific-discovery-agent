
from unittest.mock import MagicMock, patch

from services.gemini_service import generate_response


def test_gemini_response():
    """Test Gemini response without using a real API key."""

    mock_response = MagicMock()
    mock_response.text = "Scientific discovery starts with a question."

    with patch.dict(
        "os.environ",
        {"GEMINI_API_KEY": "test-key"},
    ):
        with patch("services.gemini_service.genai.Client") as mock_client:
            mock_client.return_value.models.generate_content.return_value = (
                mock_response
            )

            result = generate_response("What is scientific discovery?")

    assert result == "Scientific discovery starts with a question."
