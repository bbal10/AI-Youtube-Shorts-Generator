import asyncio
import logging
import os
from typing import Iterable

from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from mutagen.mp3 import MP3

logger = logging.getLogger(__name__)


class AudioEngine:
    def __init__(
        self,
        api_key: str,
        voice_id: str,
        model_id: str,
        stability: float,
        similarity_boost: float,
        style: float,
    ):
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY is required")
        self.voice_id = voice_id
        self.model_id = model_id
        self.voice_settings = VoiceSettings(
            stability=stability,
            similarity_boost=similarity_boost,
            style=style,
        )
        self.client = ElevenLabs(api_key=api_key)
        self.output_dir = os.path.join(os.getcwd(), "assets", "audio_clips")
        os.makedirs(self.output_dir, exist_ok=True)

    def _write_audio_file(self, text: str, output_path: str):
        audio_stream: Iterable[bytes] = self.client.text_to_speech.convert(
            text=text,
            voice_id=self.voice_id,
            model_id=self.model_id,
            output_format="mp3_44100_128",
            voice_settings=self.voice_settings,
        )

        with open(output_path, "wb") as file_handle:
            for chunk in audio_stream:
                if chunk:
                    file_handle.write(chunk)

    async def generate_audio(self, text, output_filename, retries=3):
        output_path = os.path.join(self.output_dir, output_filename)

        for attempt in range(1, retries + 1):
            try:
                await asyncio.to_thread(self._write_audio_file, text, output_path)
                return output_path
            except Exception as error:  # noqa: BLE001
                logger.warning("Audio generation failed (attempt %s/%s): %s", attempt, retries, error)
                if attempt < retries:
                    await asyncio.sleep(2)
                else:
                    raise

    def get_audio_duration(self, file_path):
        try:
            audio = MP3(file_path)
            return audio.info.length
        except Exception as error:  # noqa: BLE001
            logger.error("Error reading audio length for %s: %s", file_path, error)
            return 0.0

    async def process_script(self, script_data):
        logger.info("Starting audio generation for %s scenes", len(script_data))

        for scene in script_data:
            scene_id = scene["id"]
            text = scene["text"]
            filename = f"voice_{scene_id}.mp3"

            try:
                file_path = await self.generate_audio(text, filename)
                duration = self.get_audio_duration(file_path)
                scene["audio_path"] = file_path
                scene["duration"] = duration
                logger.info("Scene %s audio generated (%.2fs)", scene_id, duration)
                await asyncio.sleep(1)
            except Exception as error:  # noqa: BLE001
                logger.error("Skipping scene %s because audio generation failed: %s", scene_id, error)

        return script_data
