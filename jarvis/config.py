"""
jarvis/config.py
════════════════
All user-facing configuration. Edit this file — nothing else.

API keys can also be loaded from a .env file in this directory:
  GROQ_API_KEY=gsk_xxxx
"""

import os

# ── Load .env file if present ─────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass   # python-dotenv is optional

# ── API Keys ──────────────────────────────────────────────────────────────────
# Now strictly loads from the environment / .env file
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY is not set. Please add it to your .env file.")

# ── Wake trigger ──────────────────────────────────────────────────────────────
# "clap"    — double clap (fully offline, no keys, no signup)
# "keyword" — openwakeword model  (also offline, no keys, no signup)
# "voice"   — uses existing STT to listen for "Hey Jarvis"
WAKE_MODE = "clap"

# Startup behavior
# True: activate immediately on launch, speak the technology briefing, then begin normal conversation.
# False: wait for the configured wake trigger before speaking/listening.
AUTO_START_CONVERSATION = True
STARTUP_TECH_BRIEFING = True

# ── Premium Intelligence Configuration ─────────────────────────────────────────────
# Balanced for intelligent, contextual responses with Jarvis personality
PREMIUM_INTELLIGENCE = True
CLAP_DOUBLE = False        # Single clap only when wake detection is explicitly enabled
CLAP_MIN_GAP_MS = 150      # Minimum gap between claps (optimized precision)
CLAP_MAX_GAP_MS = 600      # Maximum gap between claps (premium window)
CLAP_SENSITIVITY = 2.8     # Optimized sensitivity for high precision

# ── Technology News Configuration ────────────────────────────────────────────────
# Enable intelligent news summarization using the Groq brain
INTELLIGENT_NEWS_SUMMARY = True

# Number of headlines to fetch for processing (more headlines = better summaries)
NEWS_HEADLINE_COUNT = 5

# News categories to focus on (comma-separated string)
NEWS_CATEGORIES = "technology,artificial intelligence,machine learning,chips,cybersecurity,startups,software,cloud computing"

# Minimum headline length to filter out short/low-quality content
MIN_HEADLINE_LENGTH = 15

# Enable filtering of promotional/sponsored content
FILTER_PROMOTIONAL_CONTENT = True

# Disable tech briefing after consecutive network errors (prevents startup delays)
DISABLE_BRIEFING_ON_NETWORK_ERROR = False

# News briefing style: "single" for one major story with global context, "multiple" for several headlines, "60second" for comprehensive briefing
NEWS_BRIEFING_STYLE = "60second"

# Automatically open Electron HUD when Jarvis comes online
AUTO_OPEN_HUD = True

# Only used when WAKE_MODE = "keyword"
# Built-in options (no download): "alexa", "hey_mycroft", "hey_rhasspy"
# Custom model:  path to your trained .onnx file, e.g. "./models/hey_jarvis.onnx"
# 
# CURRENT SETUP: Uses "hey_mycroft" - say "Hey Mycroft" to wake Jarvis
# TO USE "Hey Jarvis": Run python train_hey_jarvis.py to train a custom model
KEYWORD_MODEL     = "hey_mycroft"
KEYWORD_THRESHOLD = 0.5    # 0.0–1.0; lower = more sensitive

# ── Clap detector tuning ──────────────────────────────────────────────────────
CLAP_SENSITIVITY      = 2.8    # Premium precision optimized

# ── Intelligence Tuning ──────────────────────────────────────────────────────
# These values MUST be high enough for Jarvis to produce intelligent responses.
# Previously set to 80/3/0.1 which crippled output quality.
MAX_TOKENS = 512           # Full responses — Jarvis needs room to think
MEMORY_HISTORY_LIMIT = 15  # Deep context — Jarvis remembers the conversation
RESEARCH_DEPTH = "thorough" # Full research for complex questions
RESPONSE_TEMPERATURE = 0.7  # Personality + creativity — matches SOUL.md character

# ── STT ───────────────────────────────────────────────────────────────────────
WHISPER_MODEL         = "tiny.en"   # "tiny.en" (fast) | "base.en" (recommended) | "small.en"
VAD_AGGRESSIVENESS    = 2           # 0-3; higher cuts more background noise
SILENCE_CUTOFF_MS     = 700         # ms of silence before recording stops
MAX_RECORD_SECONDS    = 9

# ── LLM Brain ─────────────────────────────────────────────────────────────────
GROQ_MODEL            = "llama-3.3-70b-versatile"  # Premium intelligence — smarter reasoning, better personality

# ── TTS ───────────────────────────────────────────────────────────────────────
# Current male neural options: en-US-BrianNeural | en-US-GuyNeural | en-US-ChristopherNeural
TTS_ENGINE            = "auto"      # "auto" = Edge neural voice, then local fallback
TTS_VOICE             = "en-US-BrianNeural"
TTS_RATE              = "-5%"       # TTS speed: "-20%" slower, "+30%" faster

# ── Shutdown phrases ──────────────────────────────────────────────────────────
SHUTDOWN_PHRASES      = ("shut down", "goodbye", "power off", "go to sleep", "goodnight")

# ── HUD Overlay ───────────────────────────────────────────────────────────────
HUD_ENABLED           = True       # Start the WebSocket bridge for the Electron HUD
HUD_WS_PORT           = 6789       # Port the HUD connects to

# ── Vision (M3) ──────────────────────────────────────────────────────────────
VISION_ENABLED        = False      # Set True when YOLO/CLIP models are installed.
VISION_CAMERA_INDEX   = 0          # Default camera (0 = built-in webcam)

# ── System Commands ───────────────────────────────────────────────────────────
SYSTEM_COMMANDS_ENABLED = True     # Allow window control, volume, screenshots
SCREENSHOT_DIR        = os.path.join(os.path.expanduser("~"), "Desktop")
