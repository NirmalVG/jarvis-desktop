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
WAKE_MODE = "clap"

# Startup behavior
# True: speak the technology briefing immediately, then begin normal conversation.
# False: wait for the configured wake trigger before speaking/listening.
AUTO_START_CONVERSATION = False
STARTUP_TECH_BRIEFING = True

# ── Senior Software Engineer Speed Optimizations ───────────────────────────────────
# Ultra-fast response configuration
FAST_RESPONSE_MODE = True
CLAP_DOUBLE = True         # Double clap required for activation
CLAP_MIN_GAP_MS = 200      # Minimum gap between claps (more strict)
CLAP_MAX_GAP_MS = 500      # Maximum gap between claps (narrower window)
CLAP_SENSITIVITY = 3.5     # Even less sensitive to prevent false triggers

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
# See wake/keyword_detector.py for training instructions.
KEYWORD_MODEL     = "hey_mycroft"
KEYWORD_THRESHOLD = 0.5    # 0.0–1.0; lower = more sensitive

# ── Clap detector tuning ──────────────────────────────────────────────────────
CLAP_SENSITIVITY      = 2.0    # Ultra-sensitive for instant response (Senior Software Engineer optimized)
MAX_TOKENS = 80           # Minimized for ultra-fast responses
MEMORY_HISTORY_LIMIT = 3   # Reduced for faster recall
RESEARCH_DEPTH = "quick"   # Use quick research mode for speed
RESPONSE_TEMPERATURE = 0.1  # Low temperature for deterministic, fast responses

# ── STT ───────────────────────────────────────────────────────────────────────
WHISPER_MODEL         = "tiny.en"   # "tiny.en" (fast) | "base.en" (recommended) | "small.en"
VAD_AGGRESSIVENESS    = 2           # 0-3; higher cuts more background noise
SILENCE_CUTOFF_MS     = 700         # ms of silence before recording stops
MAX_RECORD_SECONDS    = 9

# ── LLM Brain ─────────────────────────────────────────────────────────────────
GROQ_MODEL            = "llama-3.1-8b-instant"   # Fast; swap to "llama-3.3-70b-versatile" for smarter

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
