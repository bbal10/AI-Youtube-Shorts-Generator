import json
import logging
import time
from typing import Optional

from modules.llm_providers import LLMProvider

logger = logging.getLogger(__name__)


class ContentBrain:
    def __init__(self, provider: LLMProvider, retries: int = 3, retry_delay: float = 2.0):
        self.provider = provider
        self.retries = retries
        self.retry_delay = retry_delay

    def _generate_with_retries(self, prompt: str) -> str:
        last_error: Optional[Exception] = None
        for attempt in range(1, self.retries + 1):
            try:
                return self.provider.generate(prompt)
            except Exception as error:  # noqa: BLE001
                last_error = error
                logger.warning("LLM generation failed (attempt %s/%s): %s", attempt, self.retries, error)
                if attempt < self.retries:
                    time.sleep(self.retry_delay)
        raise RuntimeError("LLM generation failed after retries") from last_error

    def get_trending_topic(self) -> str:
        prompt = (
            "Give me 1 specific, viral, and engaging topic for a Short Documentary. "
            "It should be a 'Engaging Did you know' fact or a 'Fun/intriguing Engaging News'. "
            "return ONLY the topic name."
        )
        topic = self._generate_with_retries(prompt).strip()
        logger.info("Selected topic: %s", topic)
        return topic

    def generate_script(self, topic: str):
        logger.info("Generating script for topic: %s", topic)
        prompt = f"""
You are the lead scriptwriter for a high-retention "Edutainment" YouTube Shorts channel.
Topic: {topic}

### GOAL:
Create a script where every sentence has a "Visual Switch".
To keep retention high, we need TWO different visuals for every single scene.

### 1. SCRIPT REQUIREMENTS (The Voiceover):
- **Perspective:** Strictly **3rd Person** ("Scientists found...", "The ocean hides...").
- **Tone:** Engaging, fast-paced, logical. No fluff.
- **Structure:** 8-9 Scenes total.
- **Flow:** Hook -> Context -> Mechanism (How it works) -> Twist -> Outro.

### 2. VISUAL REQUIREMENTS (Dual Visuals):
- For EVERY scene, provide TWO distinct search terms:
  - **visual_1:** Matches the *start* of the sentence.
  - **visual_2:** Matches the *end* of the sentence or provides a reaction/context.
- **Strictly Literal:** If the text is "The economy crashed," do NOT search "sad man". Search "Stock market red chart".

### OUTPUT FORMAT (Strict JSON):
[
    {{
        "id": 1,
        "text": "In 1995, fourteen wolves were released into Yellowstone Park, and they changed the rivers.",
        "visual_1": "wolves running snow aerial",
        "visual_2": "river flowing forest drone",
        "mood": "intriguing"
    }},
    {{
        "id": 2,
        "text": "It sounds impossible, but the biology is actually simple math.",
        "visual_1": "person shocked looking at camera",
        "visual_2": "blackboard math equations chalk",
        "mood": "educational"
    }}
]
"""

        raw_response = self._generate_with_retries(prompt)
        clean_text = raw_response.replace("```json", "").replace("```", "").strip()

        try:
            script_data = json.loads(clean_text)
        except json.JSONDecodeError as error:
            logger.error("Failed parsing script JSON: %s", error)
            logger.debug("Raw model response: %s", clean_text)
            return None

        return script_data
