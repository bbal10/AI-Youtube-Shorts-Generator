import logging
import os
import time
from typing import Optional

from modules.visual_providers import VisualProvider

logger = logging.getLogger(__name__)


class AssetManager:
    def __init__(self, provider: VisualProvider, fallback_provider: Optional[VisualProvider] = None):
        self.provider = provider
        self.fallback_provider = fallback_provider
        self.assets_dir = os.path.join(os.getcwd(), "assets", "generated_visuals")
        os.makedirs(self.assets_dir, exist_ok=True)

    def _generate_with_retry(self, prompt: str, duration: float, retries: int = 3) -> Optional[str]:
        last_error = None
        for attempt in range(1, retries + 1):
            try:
                result = self.provider.generate_visual(prompt, duration)
                if result:
                    return result
            except Exception as error:  # noqa: BLE001
                last_error = error
                logger.warning("Primary visual generation failed (attempt %s/%s): %s", attempt, retries, error)
            time.sleep(1)

        if self.fallback_provider:
            for attempt in range(1, retries + 1):
                try:
                    result = self.fallback_provider.generate_visual(prompt, duration)
                    if result:
                        return result
                except Exception as error:  # noqa: BLE001
                    last_error = error
                    logger.warning("Fallback visual generation failed (attempt %s/%s): %s", attempt, retries, error)
                time.sleep(1)

        if last_error:
            logger.error("Visual generation permanently failed for prompt '%s': %s", prompt, last_error)
        return None

    def get_videos(self, script_data):
        logger.info("Generating visuals for %s scenes", len(script_data))
        visual_pairs = []

        for scene in script_data:
            scene_id = scene["id"]
            duration = max(float(scene.get("duration", 6.0)), 1.0)
            half_duration = duration / 2

            query_a = scene.get("visual_1", scene.get("keywords", "abstract portrait"))
            query_b = scene.get("visual_2", query_a)

            path_a = self._generate_with_retry(query_a, half_duration)
            path_b = self._generate_with_retry(query_b, half_duration)

            if not path_a and path_b:
                path_a = path_b
                logger.warning("Scene %s visual A missing; reusing visual B", scene_id)
            if not path_b and path_a:
                path_b = path_a
                logger.warning("Scene %s visual B missing; reusing visual A", scene_id)

            if path_a and path_b:
                visual_pairs.append((path_a, path_b))
                logger.info("Scene %s visuals ready", scene_id)
            else:
                visual_pairs.append(None)
                logger.error("Scene %s visuals unavailable", scene_id)

        return visual_pairs
