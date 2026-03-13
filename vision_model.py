import base64
import io
import logging

from PIL import Image
from openai import OpenAI

from CONFIG import VISION_URL, VISION_MODEL, VLLM_API_KEY, VISION_MAX_TOKENS
from PROMPTS import VISION_FIRST_FRAME, VISION_SUBSEQUENT_FRAME

logger = logging.getLogger(__name__)


def _build_prompt(descriptions: list) -> str:
    """Build the vision prompt for the current frame.

    Args:
        descriptions: List of prior frame description dicts with 'timestamp' and 'description' keys.

    Returns:
        Prompt string incorporating prior frame history if available.
    """
    if not descriptions:
        return VISION_FIRST_FRAME
    history = "\n".join(
        f"[{d['timestamp']}] {d['description']}" for d in descriptions
    )
    return VISION_SUBSEQUENT_FRAME.format(history=history)


def analyze_frames(frames: list) -> list:
    """Analyze video frames with the vision model and return timestamped descriptions.

    Args:
        frames: List of frame dicts with 'path', 'index', and 'timestamp' keys.

    Returns:
        List of dicts with 'frame', 'timestamp', and 'description' keys.
    """
    client = OpenAI(base_url=VISION_URL, api_key=VLLM_API_KEY)
    descriptions = []

    for i, frame_data in enumerate(frames):
        logger.info("Analyzing frame %d/%d...", i + 1, len(frames))

        img = Image.open(frame_data["path"])
        img.thumbnail((768, 768))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        img_b64 = base64.b64encode(buf.getvalue()).decode()

        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": _build_prompt(descriptions)},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                        },
                    ],
                }
            ],
            max_tokens=VISION_MAX_TOKENS,
        )

        descriptions.append(
            {
                "frame": frame_data["index"],
                "timestamp": f"{int(frame_data['timestamp']//60)}:{int(frame_data['timestamp']%60):02d}",
                "description": response.choices[0].message.content,
            }
        )

    return descriptions
