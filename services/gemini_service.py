
import os
import time

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai.errors import ServerError

load_dotenv()


def generate_response(prompt: str) -> str:
    """Generate a Gemini response with retries and model fallback."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing. Please configure your environment."
        )

    client = genai.Client(api_key=api_key)

    primary_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    fallback_model = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite")

    models = list(dict.fromkeys([primary_model, fallback_model]))

    for model in models:
        for attempt in range(1, 4):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )

                if not response.text:
                    raise RuntimeError("Gemini returned an empty response.")

                return response.text

            except (ServerError, httpx.TransportError) as error:
                if isinstance(error, ServerError) and error.code != 503:
                    raise

                if attempt == 3:
                    print(
                        f"Model {model} unavailable after retries.",
                        flush=True,
                    )
                    break

                delay = 5 * attempt
                print(
                    f"Temporary error with {model}. "
                    f"Retrying in {delay} seconds...",
                    flush=True,
                )
                time.sleep(delay)

    raise RuntimeError(
        "All configured Gemini models failed after retries."
    )
