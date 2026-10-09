
import os

from dotenv import load_dotenv
from google import genai

# Load environment variables from .env
load_dotenv()


def generate_response(prompt: str) -> str:
    """Generate a response using the Gemini API."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing. "
            "Please configure your .env file."
        )

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return response.text
