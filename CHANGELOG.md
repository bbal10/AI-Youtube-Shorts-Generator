# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased] — Production-Ready Refactor

### Added

#### Configuration & Secrets Management
- `config.py` — Centralized `AppConfig` dataclass that loads **all** settings from environment variables via `python-dotenv`. No more hardcoded values anywhere in the codebase.
- `.env.example` — Template listing every required environment variable (AI keys, ElevenLabs settings, visual provider keys, render settings, subtitle options). Copy to `.env` and fill in your credentials.
- `requirements.txt` — Explicit dependency manifest (`anthropic`, `elevenlabs`, `ffmpeg-python`, `google-genai`, `mutagen`, `openai`, `python-dotenv`, `replicate`, `requests`).

#### LLM Provider Abstraction (`modules/llm_providers.py`)
- `LLMProvider` — Abstract base class with a single `generate(prompt: str) -> str` method.
- `GeminiProvider` — Google Gemini backend (wraps `google-genai`).
- `OpenAIProvider` — OpenAI backend supporting GPT-4o and other chat models.
- `AnthropicProvider` — Anthropic Claude backend with configurable `max_tokens`.
- Active provider is selected via `AI_PROVIDER` env var (`gemini` | `openai` | `anthropic`); model via `AI_MODEL`.

#### ElevenLabs Audio Engine (`modules/audio.py`)
- Replaced `edge-tts` with the official **ElevenLabs SDK**.
- `AudioEngine` now accepts `voice_id`, `model_id`, `stability`, `similarity_boost`, and `style` — all pulled from config.
- Audio is streamed in chunks and written to disk as MP3 (format: `mp3_44100_128`).
- Retry logic (3 attempts with 2-second back-off) is retained.
- Rate-limit courtesy sleep (1 second between scenes) is retained.
- `get_audio_duration()` still uses `mutagen.mp3.MP3`.
- Async interface (`process_script`) is unchanged.

#### Visual Provider Abstraction (`modules/visual_providers.py`)
- `VisualProvider` — Abstract base class with `generate_visual(prompt, duration) -> str | None`.
- `StabilityAIProvider` — Generates 9:16 portrait JPEG stills via Stability AI Core API.
- `ReplicateProvider` — Runs any Replicate model (default: `black-forest-labs/flux-schnell`) for image or video generation.
- `PexelsProvider` — Original Pexels stock-video download logic extracted here as the recommended **fallback** provider.
- All providers write to `assets/generated_visuals/`.

#### Asset Manager Refactor (`modules/asset_manager.py`)
- `AssetManager` now accepts a primary `VisualProvider` and an optional `fallback_provider` via dependency injection.
- Retry loop (3 attempts) automatically falls back to the fallback provider if the primary fails.
- Preserves the dual A/B visual-per-scene strategy and self-healing fallback (use A for both if B is missing, and vice versa).

#### Composer — Timeline Engine & Smart Composition (`modules/composer.py`)
- `Timeline` / `TimelineSegment` dataclasses track every visual segment with `start_time`, `end_time`, `visual_path`, `audio_path`, and `transition_type`.
- `create_timeline()` auto-calculates cumulative offsets so scenes start exactly when the previous ends (minus transition overlap).
- **Ken Burns effect** — For still images (`.jpg`, `.jpeg`, `.png`, `.webp`), a slow `zoompan` filter is applied automatically to create motion. Video clips use the original trim+scale pipeline.
- **Mood-based transitions** instead of purely random picks:
  - `"intriguing"` / `"mystery"` → `fade`
  - `"educational"` → `diagbr` or `wipeleft`
  - `"ominous"` / `"dramatic"` → `fadeblack`
  - Everything else → random from available transitions
- **Subtitle overlay** — Each scene's `text` is burned into the video via FFmpeg `drawtext` (bold white text with black border/shadow, centered at the bottom third). Position (`SUBTITLE_Y_RATIO`) and font size (`SUBTITLE_FONT_SIZE`) are configurable.
- `Composer` constructor now accepts `width`, `height`, `fps`, `transition_duration`, `subtitle_y_ratio`, and `subtitle_font_size` for full renderability control.
- `render_all_scenes()` returns `(rendered_paths, transitions)` so transitions are computed once and reused during stitching.
- `concatenate_with_transitions()` signature updated to accept the pre-computed `transitions` list.

#### Main Orchestrator CLI (`main.py`)
- Loads `AppConfig.from_env()` at startup.
- Builds the correct LLM provider and visual provider based on config (or CLI override).
- Passes all providers to modules via constructor injection.
- `argparse` CLI with the following flags:
  - `--topic` — Provide a topic manually instead of letting AI pick one.
  - `--ai-provider` — Override the configured LLM provider (`gemini`, `openai`, `anthropic`).
  - `--visual-provider` — Override the configured visual provider (`stability`, `replicate`, `pexels`).
  - `--output` — Set the output filename (default: `final_short.mp4`).
- End-of-run summary log: total video duration, file size in MB, output path.
- Structured logging (`logging.basicConfig`) replaces all bare `print()` calls.

### Changed

- **`modules/brain.py`** — `ContentBrain` now takes an `LLMProvider` as its first constructor argument. Prompt engineering and JSON output format (`id`, `text`, `visual_1`, `visual_2`, `mood`) are unchanged.
- **`modules/audio.py`** — TTS backend changed from `edge-tts` to ElevenLabs; output format stays MP3.
- **`modules/asset_manager.py`** — Output directory changed from `assets/video_clips/` to `assets/generated_visuals/` to reflect that visuals can now be AI-generated, not just downloaded.
- **`main.py`** — Full rewrite of orchestration logic to support config-driven providers, CLI flags, and structured logging.
- **`README.md`** — Updated setup instructions, feature list, and CLI usage examples to reflect the new architecture.
- **`.gitignore`** — Added `__pycache__/` and `*.pyc` patterns to prevent accidental commits of bytecode.

### Removed

- `modules/test.py` — Empty placeholder, no longer needed.
- `modules/test-audi.py` — Diagnostic test for the old Bark/Ngrok audio setup; superseded by ElevenLabs.
- `modules/notneededaudio.py` — Bark-via-Colab audio implementation; superseded by ElevenLabs.
- Hardcoded Gemini API key from `modules/brain.py` line 7.
- Hardcoded Pexels API key from `modules/asset_manager.py` line 8.
- Avatar injection logic from `modules/composer.py` (avatar mode was removed as part of the timeline refactor).

---

## [Previous] — Original Release

Initial pipeline using:
- Google Gemini (`gemini-3-flash-preview`) for script generation.
- `edge-tts` with `en-US-AvaNeural` voice for TTS.
- Pexels API for stock video download.
- FFmpeg for scene rendering and stitching with random `xfade` transitions.
