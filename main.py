import argparse
import asyncio
import logging
import os
import shutil

from config import AppConfig
from modules.asset_manager import AssetManager
from modules.audio import AudioEngine
from modules.brain import ContentBrain
from modules.composer import Composer
from modules.llm_providers import AnthropicProvider, GeminiProvider, OpenAIProvider
from modules.visual_providers import PexelsProvider, ReplicateProvider, StabilityAIProvider

logger = logging.getLogger(__name__)


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def clean_cache():
    logger.info("Cleaning temporary workspace folders")
    folders_to_clean = [
        os.path.join(os.getcwd(), "assets", "audio_clips"),
        os.path.join(os.getcwd(), "assets", "temp"),
    ]

    for folder in folders_to_clean:
        if not os.path.exists(folder):
            continue

        if "assets" not in folder:
            logger.warning("Skipping potentially unsafe path: %s", folder)
            continue

        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except OSError as error:
                logger.error("Failed to remove %s: %s", file_path, error)


def build_llm_provider(config: AppConfig, provider_name: str):
    provider = provider_name.lower()
    if provider == "gemini":
        return GeminiProvider(config.gemini_api_key, config.ai_model)
    if provider == "openai":
        return OpenAIProvider(config.openai_api_key, config.ai_model)
    if provider == "anthropic":
        return AnthropicProvider(config.anthropic_api_key, config.ai_model, config.anthropic_max_tokens)
    raise ValueError(f"Unsupported AI provider: {provider_name}")


def build_visual_provider(config: AppConfig, provider_name: str):
    output_dir = os.path.join(os.getcwd(), "assets", "generated_visuals")
    os.makedirs(output_dir, exist_ok=True)

    provider = provider_name.lower()
    if provider == "stability":
        primary = StabilityAIProvider(config.stability_api_key, output_dir)
    elif provider == "replicate":
        primary = ReplicateProvider(config.replicate_api_token, config.replicate_model, output_dir)
    elif provider == "pexels":
        primary = PexelsProvider(config.pexels_api_key, output_dir)
    else:
        raise ValueError(f"Unsupported visual provider: {provider_name}")

    fallback = None
    if provider != "pexels" and config.pexels_api_key:
        fallback = PexelsProvider(config.pexels_api_key, output_dir)

    return primary, fallback


def parse_args():
    parser = argparse.ArgumentParser(description="AI YouTube Shorts pipeline")
    parser.add_argument("--topic", help="Manual topic override")
    parser.add_argument("--ai-provider", choices=["gemini", "openai", "anthropic"], help="Override AI provider")
    parser.add_argument("--visual-provider", choices=["stability", "replicate", "pexels"], help="Override visual provider")
    parser.add_argument("--output", default="final_short.mp4", help="Output filename")
    return parser.parse_args()


async def run_pipeline():
    configure_logging()
    args = parse_args()
    config = AppConfig.from_env()

    ai_provider_name = args.ai_provider or config.ai_provider
    visual_provider_name = args.visual_provider or config.visual_provider

    logger.info("Starting automation (AI provider: %s, Visual provider: %s)", ai_provider_name, visual_provider_name)

    llm_provider = build_llm_provider(config, ai_provider_name)
    visual_provider, visual_fallback = build_visual_provider(config, visual_provider_name)

    brain = ContentBrain(provider=llm_provider)
    audio_engine = AudioEngine(
        api_key=config.elevenlabs_api_key,
        voice_id=config.elevenlabs_voice_id,
        model_id=config.elevenlabs_model_id,
        stability=config.elevenlabs_stability,
        similarity_boost=config.elevenlabs_similarity_boost,
        style=config.elevenlabs_style,
    )
    asset_manager = AssetManager(provider=visual_provider, fallback_provider=visual_fallback)
    composer = Composer(
        width=config.output_width,
        height=config.output_height,
        fps=config.fps,
        transition_duration=config.transition_duration,
        subtitle_y_ratio=config.subtitle_y_ratio,
        subtitle_font_size=config.subtitle_font_size,
    )

    topic = args.topic or brain.get_trending_topic()
    script = brain.generate_script(topic)
    if not script:
        raise RuntimeError("Script generation returned no scenes")

    script = await audio_engine.process_script(script)
    script = [scene for scene in script if scene.get("audio_path") and scene.get("duration", 0) > 0]
    if not script:
        raise RuntimeError("No scenes with valid audio")

    assets_map = asset_manager.get_videos(script)
    rendered_scene_paths, transitions = composer.render_all_scenes(script, assets_map)
    final_output = composer.concatenate_with_transitions(rendered_scene_paths, transitions, output_filename=args.output)

    if not final_output:
        raise RuntimeError("Video composition failed")

    total_duration = composer.get_duration(final_output)
    file_size = os.path.getsize(final_output)
    logger.info(
        "Pipeline finished | Duration: %.2fs | File Size: %.2f MB | Output: %s",
        total_duration,
        file_size / (1024 * 1024),
        final_output,
    )

    clean_cache()


if __name__ == "__main__":
    try:
        asyncio.run(run_pipeline())
    except Exception as error:  # noqa: BLE001
        logger.exception("Pipeline failed: %s", error)
        raise
