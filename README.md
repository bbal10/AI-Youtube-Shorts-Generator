# 🎬 AutoShorts AI: The Automated Faceless Video Generator

![Views](https://komarev.com/ghpvc/?username=SaarD00-AI-Youtube-Shorts-Generator&style=for-the-badge&color=blue)


**AutoShorts AI** is a fully automated Python pipeline that creates viral-style "Faceless" YouTube Shorts and TikToks from a single topic. It handles the entire production chain: researching, scriptwriting, voiceover generation, stock footage sourcing, and advanced video editing with transitions and avatar injection.

---

## ✨ Key Features

- **🧠 Intelligent Scriptwriting:** Configurable LLM provider abstraction with **Gemini**, **OpenAI**, or **Anthropic** backends.
- **🗣️ Human-Like Voiceovers:** **ElevenLabs** voice generation with configurable `voice_id`, model, and voice settings.
- **🎞️ Dual-Visual System:** Configurable visual providers: **Stability AI** (image generation), **Replicate** (video/image generation), and **Pexels** fallback.
- **✂️ Advanced FFmpeg Editing:**
- **Smart Trimming:** Syncs video perfectly to audio duration.
- **A/B Splitting:** Cuts every scene in half, switching visuals mid-sentence.
- **Pro Transitions:** Randomly applies `xfade` (fade, slide, wipes) between scenes.
- **Silence Removal:** Automatically trims dead air from AI voice generation.

- **🪟 Windows Ready:** Includes specific FFmpeg flags (`yuv420p`, `faststart`) to prevent corruption errors (`0x80004005`) on Windows Media Player.
- **🧩 Production Configuration:** Centralized app configuration via `config.py` and environment variables in `.env`.

---

## 📂 Project Structure

```text
Automated-YT-Shorts-AI/
│
├── assets/                  # Stores all media files
│   ├── audio_clips/         # Generated voiceovers (.wav)
│   ├── video_clips/         # Downloaded stock footage (.mp4)
│   ├── temp/                # Intermediate processing files
│   ├── final/               # 🏆 The Final Output Video lives here
│   └── avatar/              # ⚠️ PUT YOUR AVATAR VIDEO HERE
│       └── Professional_Girl_Animation_Video_Generation.mp4
│
├── modules/                 # Core Logic Modules
│   ├── brain.py             # AI Scriptwriter (Gemini)
│   ├── audio.py             # Voice Generator (Bark Client)
│   ├── asset_manager.py     # Pexels Downloader (Dual-Visual logic)
│   └── composer.py          # FFmpeg Video Editor (Stitching & Transitions)
│
├── main.py                  # Entry point (Orchestrator)
├── test_audio.py            # Diagnostic tool for Bark connection
└── requirements.txt         # Python dependencies

```

---

## 🛠️ Prerequisites

1. **Python 3.10+** installed.
2. **FFmpeg** installed and added to your system PATH.

- _Windows:_ `winget install ffmpeg` (or download from [ffmpeg.org](https://ffmpeg.org/download.html)).
- _Verify:_ Type `ffmpeg -version` in your terminal.

3. **API Keys / Tokens** (based on your selected providers):
- Gemini / OpenAI / Anthropic API key
- ElevenLabs API key
- Stability API key and/or Replicate API token
- Pexels API key (recommended as fallback)

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/AutoShorts-AI.git
cd AutoShorts-AI

```

### 2. Install Dependencies

```bash
pip install -r requirements.txt

```

_(If `requirements.txt` is missing, install manually: `pip install google-generativeai requests ffmpeg-python mutagen colorama`)_

### 3. Environment Setup

Copy `.env.example` to `.env` and fill provider keys/settings:

```bash
cp .env.example .env
```

All secrets are read from environment variables (no hardcoded API keys).

---

## 🎮 How to Run

Run the main script:

```bash
python main.py
```

Or use CLI overrides:

```bash
python main.py --topic "Ancient Rome engineering" --ai-provider openai --visual-provider stability --output my_short.mp4
```

The final video is saved to `assets/final/`.

---

## 🧩 Module Breakdown

### `brain.py` ( The Writer)

- **Input:** Topic string.
- **Logic:** Prompts Gemini to create an 8-9 scene JSON script. It asks for **two** visual keywords per scene (`visual_1`, `visual_2`) to enable the A/B split effect.

### `audio.py` (The Voice)

- **Input:** Text script.
- **Logic:** Sends text to the Colab server. Includes a "Confidence" setting (`text_temp=0.7`) to make the voice sound like an influencer.
- **Post-Processing:** Uses FFmpeg to trim silence and boost volume (2x).

### `asset_manager.py` (The Librarian)

- **Input:** Visual keywords.
- **Logic:** Searches Pexels for **Portrait (9:16)** videos. Downloads pairs of videos for every scene. Handles fallbacks (if Video B is missing, reuse Video A).

### `composer.py` (The Editor)

- **Input:** Audio files + Video files.
- **Logic:**
- **Scene Processing:** Cuts the scene duration in half. Plays Video A for the first half, Video B for the second half.
- **Avatar Injection:** Identifies a random "middle" scene (not hook/outro) and replaces the stock footage with your Avatar loop.
- **Stitching:** Merges all scenes using `xfade` transitions (wipes, slides).
- **Rendering:** Exports as `yuv420p` H.264 MP4 with `faststart` flags for maximum compatibility.

---

## ⚠️ Troubleshooting

**Q: The video is black or corrupt (0x80004005 error).**

- **Fix:** This is usually a Windows codec issue. The updated `composer.py` forces `pix_fmt='yuv420p'`. Try opening the file with VLC Media Player.

**Q: "Avatar file missing" error.**

- **Fix:** Altough not needed, Ensure your folder structure is exactly `assets/avatar/avatar.mp4`.

**Q: The audio is silent or fails.**

- **Fix:** Your Ngrok tunnel likely expired. Restart the Colab cell and update the URL in `audio.py`.

**Q: FFmpeg error "Exec format error" or "not found".**

- **Fix:** Ensure FFmpeg is installed and accessible from your command line.

---

## 📜 License

This project is open-source. Feel free to modify and build your own automation empire!
