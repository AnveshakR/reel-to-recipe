import logging

import requests

from CONFIG import WHISPER_URL

logger = logging.getLogger(__name__)


def transcribe_audio(audio_path: str) -> str:
    """Transcribe an audio file using the Whisper ASR service.

    Args:
        audio_path: Path to the audio file to transcribe.

    Returns:
        Plain-text transcript string.
    """
    logger.info("Transcribing audio...")

    with open(audio_path, "rb") as f:
        response = requests.post(
            WHISPER_URL,
            files={"audio_file": f},
            data={"task": "transcribe", "language": "en"},
        )

    response.raise_for_status()
    return response.text.strip()
