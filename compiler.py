import logging
import re
from datetime import datetime

from openai import OpenAI

from CONFIG import (
    TEXT_URL,
    TEXT_MODEL,
    VLLM_API_KEY,
    TEXT_MAX_TOKENS_DOC,
    TEXT_MAX_TOKENS_NAME,
)
from PROMPTS import COMPILE_DOCUMENT, GENERATE_RECIPE_NAME

logger = logging.getLogger(__name__)


def compile_document(metadata: dict, frame_descriptions: list, transcript: str) -> str:
    """Compile a structured recipe Markdown document from video analysis data.

    Args:
        metadata: Video metadata dict with 'title', 'uploader', and 'description' keys.
        frame_descriptions: List of frame description dicts with 'timestamp' and 'description' keys.
        transcript: Full audio transcript string.

    Returns:
        Recipe formatted as a Markdown string, or a fallback stub on failure.
    """
    client = OpenAI(base_url=TEXT_URL, api_key=VLLM_API_KEY)

    visual_timeline = "\n".join(
        [f"[{fd['timestamp']}] {fd['description']}" for fd in frame_descriptions]
    )

    prompt = COMPILE_DOCUMENT.format(
        title=metadata.get("title", "Unknown"),
        uploader=metadata.get("uploader", "Unknown"),
        description=metadata.get("description", "No description"),
        visual_timeline=visual_timeline,
        transcript=transcript,
    )

    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=TEXT_MAX_TOKENS_DOC,
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("Model returned no content")
        content = content.strip()
        if content.startswith("```"):
            content = re.sub(r"^```[a-zA-Z]*\n?", "", content)
            content = re.sub(r"\n?```$", "", content)
        return content.strip()
    except Exception:
        logger.exception("Failed to compile recipe document")
        return "# Recipe\n\n*Recipe compilation failed.*"


def generate_recipe_name(recipe_document: str) -> str:
    """Generate a short, filename-safe recipe name from a compiled recipe document.

    Args:
        recipe_document: Full Markdown recipe string.

    Returns:
        Underscore-separated Title Case name safe for use as a filename, or a timestamped fallback on failure.
    """
    client = OpenAI(base_url=TEXT_URL, api_key=VLLM_API_KEY)

    prompt = GENERATE_RECIPE_NAME.format(recipe_document=recipe_document)

    try:
        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=TEXT_MAX_TOKENS_NAME,
        )
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("Model returned no content")
        safe = re.sub(r"[^\w\s-]", "", content.strip()).strip().replace(" ", "_")
        return safe or f"recipe_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    except Exception:
        logger.exception("Failed to generate recipe name")
        return f"recipe_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
