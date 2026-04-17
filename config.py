import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class AppConfig:
    ai_provider: str
    ai_model: str
    gemini_api_key: str
    openai_api_key: str
    anthropic_api_key: str
    anthropic_max_tokens: int

    elevenlabs_api_key: str
    elevenlabs_voice_id: str
    elevenlabs_model_id: str
    elevenlabs_stability: float
    elevenlabs_similarity_boost: float
    elevenlabs_style: float

    visual_provider: str
    stability_api_key: str
    replicate_api_token: str
    replicate_model: str
    pexels_api_key: str

    output_width: int
    output_height: int
    fps: int
    transition_duration: float
    subtitle_y_ratio: float
    subtitle_font_size: int

    @classmethod
    def from_env(cls) -> "AppConfig":
        load_dotenv()
        return cls(
            ai_provider=os.getenv("AI_PROVIDER", "gemini").lower(),
            ai_model=os.getenv("AI_MODEL", "gemini-2.0-flash"),
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            anthropic_max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "2000")),
            elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY", ""),
            elevenlabs_voice_id=os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL"),
            elevenlabs_model_id=os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"),
            elevenlabs_stability=float(os.getenv("ELEVENLABS_STABILITY", "0.5")),
            elevenlabs_similarity_boost=float(os.getenv("ELEVENLABS_SIMILARITY_BOOST", "0.75")),
            elevenlabs_style=float(os.getenv("ELEVENLABS_STYLE", "0.0")),
            visual_provider=os.getenv("VISUAL_PROVIDER", "pexels").lower(),
            stability_api_key=os.getenv("STABILITY_API_KEY", ""),
            replicate_api_token=os.getenv("REPLICATE_API_TOKEN", ""),
            replicate_model=os.getenv("REPLICATE_MODEL", "black-forest-labs/flux-schnell"),
            pexels_api_key=os.getenv("PEXELS_API_KEY", ""),
            output_width=int(os.getenv("OUTPUT_WIDTH", "1080")),
            output_height=int(os.getenv("OUTPUT_HEIGHT", "1920")),
            fps=int(os.getenv("OUTPUT_FPS", "30")),
            transition_duration=float(os.getenv("TRANSITION_DURATION", "0.5")),
            subtitle_y_ratio=float(os.getenv("SUBTITLE_Y_RATIO", "0.72")),
            subtitle_font_size=int(os.getenv("SUBTITLE_FONT_SIZE", "52")),
        )
