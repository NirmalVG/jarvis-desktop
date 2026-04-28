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

# Only used when WAKE_MODE = "keyword"
# Built-in options (no download): "alexa", "hey_mycroft", "hey_rhasspy"
# Custom model:  path to your trained .onnx file, e.g. "./models/hey_jarvis.onnx"
# See wake/keyword_detector.py for training instructions.
KEYWORD_MODEL     = "hey_mycroft"
KEYWORD_THRESHOLD = 0.5    # 0.0–1.0; lower = more sensitive

# ── Clap detector tuning ──────────────────────────────────────────────────────
CLAP_SENSITIVITY      = 3.0    # Energy multiplier above noise floor (lower = more sensitive)
CLAP_DOUBLE           = True   # Require double clap (reduces false positives)
CLAP_MIN_GAP_MS       = 150    # Minimum gap between claps
CLAP_MAX_GAP_MS       = 800    # Maximum gap between claps

# ── STT ───────────────────────────────────────────────────────────────────────
WHISPER_MODEL         = "base.en"   # "tiny.en" (fast) | "base.en" (recommended) | "small.en"
VAD_AGGRESSIVENESS    = 2           # 0-3; higher cuts more background noise
SILENCE_CUTOFF_MS     = 700         # ms of silence before recording stops
MAX_RECORD_SECONDS    = 9

# ── LLM Brain ─────────────────────────────────────────────────────────────────
GROQ_MODEL            = "llama-3.1-8b-instant"   # Fast; swap to "llama-3.3-70b-versatile" for smarter

# ── TTS ───────────────────────────────────────────────────────────────────────
# Options: en-US-GuyNeural | en-US-DavisNeural (deeper) | en-US-TonyNeural (casual)
TTS_VOICE             = "en-US-DavisNeural"
TTS_RATE              = "+0%"       # TTS speed: "-20%" slower, "+30%" faster

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
