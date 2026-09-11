from pathlib import Path

import openai

from api.core.logging_config import get_logger

client = openai.OpenAI()
logger = get_logger(__name__)


def llm_pipeline(file_path: Path):
    with file_path.open("rb") as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="verbose_json",
        )
        logger.info(f"Text: {response.text}")
        logger.info("Printing segments:...")
        for segment in response.segments:
            print(f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}")
