
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




import pytest
import httpx


def test_missing_api_key():
    with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
        with pytest.raises(ValueError, match="GEMINI_API_KEY is missing"):
            generate_response("Test prompt")


def test_empty_gemini_response():
    mock_response = MagicMock()
    mock_response.text = ""

    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
        with patch("services.gemini_service.genai.Client") as mock_client:
            mock_client.return_value.models.generate_content.return_value = (
                mock_response
            )

            with pytest.raises(RuntimeError, match="empty response"):
                generate_response("Test prompt")


def test_retry_after_network_error():
    mock_response = MagicMock()
    mock_response.text = "Recovered successfully"

    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
        with patch("services.gemini_service.genai.Client") as mock_client:
            with patch("services.gemini_service.time.sleep") as mock_sleep:
                mock_generate = (
                    mock_client.return_value.models.generate_content
                )
                mock_generate.side_effect = [
                    httpx.ConnectError("Temporary connection failure"),
                    mock_response,
                ]

                result = generate_response("Test prompt")

    assert result == "Recovered successfully"
    assert mock_generate.call_count == 2
    mock_sleep.assert_called_once_with(5)



def test_network_error_after_all_retries():
    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
        with patch("services.gemini_service.genai.Client") as mock_client:
            with patch("services.gemini_service.time.sleep") as mock_sleep:
                mock_generate = (
                    mock_client.return_value.models.generate_content
                )
                mock_generate.side_effect = httpx.ConnectError(
                    "Connection unavailable"
                )

                with pytest.raises(
                    RuntimeError,
                    match="All configured Gemini models failed after retries",
                ):
                    generate_response("Test prompt")

    assert mock_generate.call_count == 6
    assert mock_sleep.call_count == 4
    assert [call.args[0] for call in mock_sleep.call_args_list] == [
        5, 10, 5, 10
    ]


