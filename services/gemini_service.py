
import os
import time

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError

load_dotenv()


def generate_response(prompt: str) -> str:
    """Generate a Gemini response with retries for temporary errors."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing. Please configure your environment."
        )

    client = genai.Client(api_key=api_key)

    max_attempts = 3

    for attempt in range(1, max_attempts + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )

            if not response.text:
                raise RuntimeError("Gemini returned an empty response.")

            return response.text

        except (ServerError, httpx.TransportError) as error:
            if isinstance(error, ServerError) and error.code != 503:
                raise

            if attempt == max_attempts:
                raise

            delay = 5 * attempt
            print(
                f"Temporary Gemini API error: {type(error).__name__}. "
                f"Retrying in {delay} seconds...",
                flush=True,
            )
            time.sleep(delay)
