"""
jarvis/main.py
══════════════
Entry point.  Boots all subsystems, runs the main voice loop.

Session lifecycle:
  boot()              — initialises all modules once
  wake_fn()           — blocks until double-clap (or wake word)
  loop → stt → brain → actuator → tts
  "goodbye" → clean shutdown

Features:
  • SEARCH action handling (brain emits [SEARCH:] tags)
  • System commands: minimize, maximize, screenshot, volume
  • Vision integration (optional — VISION_ENABLED in config)
  • --no-wake CLI flag for dev/testing (skips clap detection)
  • Cleaner exception handling — distinguishes keyboard interrupt vs crash
  • Session stats shown at boot so you can see memory growing over time

HUD Integration:
  WebSocket bridge on ws://localhost:6789
  States emitted: SLEEPING → LISTENING → THINKING → SPEAKING
"""

import sys
import re
import os

# Fix Windows console encoding for emoji characters
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import config as cfg
from actuation.actions import Actuator
from brain.groq_brain  import GroqBrain
from memory.store      import MemoryStore
from services.web_search import format_results, search_web, technology_headlines
from voice.stt         import STT
from voice.tts         import TTS

# ── HUD bridge ────────────────────────────────────────────────────────────────

_bridge = None


def _init_bridge():
    global _bridge
    if not cfg.HUD_ENABLED:
        print("  🖥   HUD bridge disabled (HUD_ENABLED = False in config)")
        return
    try:
        from hud.bridge import HUDBridge
        _bridge = HUDBridge(port=cfg.HUD_WS_PORT)
        _bridge.start()
    except Exception as exc:
        print(f"  [WARN] HUD bridge failed to start: {exc}")
        print("         pip install websockets")


def hud_emit(state, transcript="", reply="", stats=None):
    """Thread-safe HUD broadcast. Silent no-op if bridge is off."""
    if _bridge is not None:
        try:
            _bridge.emit(state, transcript=transcript, reply=reply, stats=stats)
        except Exception:
            pass


# ── Vision (optional) ─────────────────────────────────────────────────────────

_vision = None


def _init_vision():
    global _vision
    if not cfg.VISION_ENABLED:
        print("  📷  Vision disabled (VISION_ENABLED = False in config)")
        return
    try:
        from vision.camera import VisionEngine
        _vision = VisionEngine(camera_index=cfg.VISION_CAMERA_INDEX)
        if _vision.start_capture():
            print("  📷  Vision engine active.")
        else:
            _vision = None
            print("  [WARN] Vision engine failed to start camera.")
    except Exception as exc:
        print(f"  [WARN] Vision engine failed: {exc}")
        _vision = None


# ── Boot ──────────────────────────────────────────────────────────────────────

def boot():
    print("\n⚡  Booting J.A.R.V.I.S...\n")

    print("  [1/7] Memory store...")
    store = MemoryStore()

    print("  [2/7] Speech recognition (Whisper)...")
    stt = STT(
        model_size=cfg.WHISPER_MODEL,
        vad_aggressiveness=cfg.VAD_AGGRESSIVENESS,
        silence_cutoff_ms=cfg.SILENCE_CUTOFF_MS,
        max_seconds=cfg.MAX_RECORD_SECONDS,
    )

    print("  [3/7] Voice synthesiser (edge-tts)...")
    tts = TTS(voice=cfg.TTS_VOICE, tts_rate=cfg.TTS_RATE)

    print("  [4/7] AI brain (Groq)...")
    brain = GroqBrain(api_key=cfg.GROQ_API_KEY, store=store, model=cfg.GROQ_MODEL)

    print("  [5/7] App actuator...")
    actuator = Actuator(speak_fn=tts.speak)

    print("  [6/7] HUD bridge...")
    _init_bridge()

    print("  [7/7] Vision engine...")
    _init_vision()

    skip_wake = "--no-wake" in sys.argv
    wake_fn = None if skip_wake else _build_wake_fn()

    print("\n✅  All systems online.\n")
    s = store.stats()
    print(f"  📊  Memory: {s['total_turns']} turns · {s['sessions']} sessions · {s['memories']} embeddings · {s['facts']} facts\n")
    if skip_wake:
        print("  ⚡  --no-wake mode: skipping clap detection.\n")

    hud_emit("SLEEPING", stats=s)
    return wake_fn, stt, tts, brain, actuator, store


def _build_wake_fn():
    if cfg.WAKE_MODE == "clap":
        from wake.clap_detector import ClapDetector
        det = ClapDetector(
            sensitivity=cfg.CLAP_SENSITIVITY,
            double_clap=cfg.CLAP_DOUBLE,
            double_clap_min_ms=cfg.CLAP_MIN_GAP_MS,
            double_clap_max_ms=cfg.CLAP_MAX_GAP_MS,
        )
        return det.listen
    elif cfg.WAKE_MODE == "keyword":
        from wake.keyword_detector import KeywordDetector
        det = KeywordDetector(model_name=cfg.KEYWORD_MODEL, threshold=cfg.KEYWORD_THRESHOLD)
        return det.listen
    else:
        raise ValueError(f"Unknown WAKE_MODE: {cfg.WAKE_MODE!r}. Must be 'clap' or 'keyword'.")


# ── System command fast-paths ─────────────────────────────────────────────────

_SYSTEM_COMMANDS = {
    "minimize window":  "minimize",
    "minimize":         "minimize",
    "maximize window":  "maximize",
    "maximize":         "maximize",
    "take screenshot":  "screenshot",
    "screenshot":       "screenshot",
    "take a screenshot":"screenshot",
    "capture screen":   "screenshot",
    "volume up":        "volume_up",
    "turn up":          "volume_up",
    "louder":           "volume_up",
    "volume down":      "volume_down",
    "turn down":        "volume_down",
    "quieter":          "volume_down",
    "mute":             "volume_mute",
    "unmute":           "volume_mute",
    "lock screen":      "lock",
    "lock computer":    "lock",
    "lock":             "lock",
    "what do you see":  "vision",
    "describe what you see": "vision",
    "look around":      "vision",
}


def _extract_web_query(clean: str, original: str) -> str | None:
    """Return a search query when the utterance asks for live web information."""
    starters = (
        "search web for ",
        "search the web for ",
        "search for ",
        "look up ",
        "google ",
        "find online ",
    )
    for starter in starters:
        if clean.startswith(starter):
            return original[len(starter):].strip()

    current_markers = (
        "latest ",
        "current ",
        "today ",
        "todays ",
        "recent ",
        "news ",
        "what happened ",
        "what is happening ",
    )
    if any(marker in clean for marker in current_markers):
        return original.strip()

    return None


def _answer_from_web(query: str, session_id, brain, tts, store, transcript: str) -> bool:
    """Search the web, summarize results through the brain, speak, and persist."""
    if not query:
        return False

    hud_emit("THINKING", transcript=transcript, reply="Searching the web...")
    try:
        results = search_web(query, limit=5)
        web_context = format_results(results)
        reply = brain.answer_with_web_context(
            f"Answer this using current web results: {query}",
            web_context,
            session_id,
        )
    except Exception as exc:
        reply = f"I could not reach the web just now: {exc}"
        store.save_turn("user", transcript, session_id)
        store.save_turn("assistant", reply, session_id)

    hud_emit("SPEAKING", transcript=transcript, reply=reply, stats=store.stats())
    tts.speak(reply)
    return True


def _speak_technology_briefing(brain, tts, store, session_id) -> None:
    """Fetch and speak a short current technology briefing after wake."""
    hud_emit("THINKING", reply="Scanning global technology headlines...")
    try:
        results = technology_headlines(limit=3)
        if results:
            headlines = []
            for result in results:
                source = f" from {result.source}" if result.source else ""
                headlines.append(f"{result.title}{source}")
            briefing = "Top technology signals: " + " Next: ".join(headlines)
            store.save_turn("assistant", briefing, session_id)
        else:
            briefing = "I could not find fresh technology headlines just now."
            store.save_turn("assistant", briefing, session_id)
    except Exception as exc:
        briefing = (
            "I could not reach the live technology brief just now. "
            f"Web error: {exc}"
        )
        store.save_turn("assistant", briefing, session_id)

    hud_emit("SPEAKING", reply=briefing, stats=store.stats())
    tts.speak(briefing)


def _handle_system_command(clean: str, actuator, tts, store, session_id) -> bool | None:
    """
    Handle system-level commands that bypass the LLM.
    Returns True if handled, None if not a system command.
    """
    if not cfg.SYSTEM_COMMANDS_ENABLED:
        return None

    action = _SYSTEM_COMMANDS.get(clean)
    if action is None:
        # Partial match check
        for phrase, act in _SYSTEM_COMMANDS.items():
            if phrase in clean:
                action = act
                break

    if action is None:
        return None

    if action == "minimize":
        actuator.minimize_window()
        store.save_turn("user", clean, session_id)
        store.save_turn("assistant", "Window minimized.", session_id)
        hud_emit("SPEAKING", transcript=clean, reply="Window minimized.", stats=store.stats())
    elif action == "maximize":
        actuator.maximize_window()
        store.save_turn("user", clean, session_id)
        store.save_turn("assistant", "Window maximized.", session_id)
        hud_emit("SPEAKING", transcript=clean, reply="Window maximized.", stats=store.stats())
    elif action == "screenshot":
        path = actuator.take_screenshot(cfg.SCREENSHOT_DIR)
        reply = f"Screenshot saved." if path else "Screenshot failed."
        store.save_turn("user", clean, session_id)
        store.save_turn("assistant", reply, session_id)
        hud_emit("SPEAKING", transcript=clean, reply=reply, stats=store.stats())
    elif action == "volume_up":
        actuator.volume_up()
        store.save_turn("user", clean, session_id)
        store.save_turn("assistant", "Volume up.", session_id)
        hud_emit("SPEAKING", transcript=clean, reply="Volume up.", stats=store.stats())
    elif action == "volume_down":
        actuator.volume_down()
        store.save_turn("user", clean, session_id)
        store.save_turn("assistant", "Volume down.", session_id)
        hud_emit("SPEAKING", transcript=clean, reply="Volume down.", stats=store.stats())
    elif action == "volume_mute":
        actuator.volume_mute()
        store.save_turn("user", clean, session_id)
        store.save_turn("assistant", "Mute toggled.", session_id)
        hud_emit("SPEAKING", transcript=clean, reply="Mute toggled.", stats=store.stats())
    elif action == "lock":
        actuator.lock_screen()
        store.save_turn("user", clean, session_id)
        store.save_turn("assistant", "Locking screen.", session_id)
        hud_emit("SLEEPING", transcript=clean, reply="Locking screen.", stats=store.stats())
    elif action == "vision":
        if _vision is None:
            tts.speak("Vision is not enabled. Set VISION_ENABLED to True in config.")
        else:
            hud_emit("THINKING", transcript=clean)
            description = _vision.describe_what_you_see()
            tts.speak(description)
            store.save_turn("user", clean, session_id)
            store.save_turn("assistant", description, session_id)
            hud_emit("SPEAKING", transcript=clean, reply=description, stats=store.stats())
    return True


# ── Command handler ───────────────────────────────────────────────────────────

def handle_command(user_text, session_id, brain, actuator, tts, store) -> bool:
    """
    Process one user utterance.
    Returns False if Jarvis should shut down, True to continue.
    """
    if len(user_text.strip()) < 3:
        return True   # Ignore noise / empty transcription

    print(f'\n👤  YOU: "{user_text}"')

    # Normalise for intent matching (lowercase, strip punctuation)
    clean = re.sub(r"[^\w\s]", "", user_text.lower()).strip()

    # Emit transcript to HUD
    hud_emit("THINKING", transcript=user_text)

    # ── Shutdown detection ────────────────────────────────────────────────
    if any(p in clean for p in cfg.SHUTDOWN_PHRASES):
        return False

    # ── Fast-path: system commands (minimize, screenshot, volume, etc.) ──
    result = _handle_system_command(clean, actuator, tts, store, session_id)
    if result is not None:
        return True

    web_query = _extract_web_query(clean, user_text)
    if web_query:
        return _answer_from_web(web_query, session_id, brain, tts, store, user_text)

    # ── Fast-path: "open X" ───────────────────────────────────────────────
    # Bypass the LLM entirely — saves ~300ms latency for the most common command.
    if clean.startswith("open "):
        app = clean[5:].strip()
        actuator.open_app(app)
        store.save_turn("user",      user_text,         session_id)
        store.save_turn("assistant", f"Opening {app}.", session_id)
        hud_emit("SPEAKING", transcript=user_text,
                 reply=f"Opening {app}.", stats=store.stats())
        return True

    # ── LLM path ──────────────────────────────────────────────────────────
    hud_emit("THINKING", transcript=user_text)
    reply = brain.think(user_text, session_id)
    print(f'🤖  JARVIS: "{reply}"')

    # ── Parse action tags ─────────────────────────────────────────────────

    app_name = GroqBrain.parse_open(reply)
    if app_name:
        actuator.open_app(app_name)
        hud_emit("SPEAKING", transcript=user_text,
                 reply=f"Opening {app_name}.", stats=store.stats())
        return True

    remind = GroqBrain.parse_remind(reply)
    if remind:
        actuator.set_reminder(*remind)
        hud_emit("SPEAKING", transcript=user_text,
                 reply=reply, stats=store.stats())
        return True

    search = GroqBrain.parse_search(reply)
    if search:
        return _answer_from_web(search, session_id, brain, tts, store, user_text)

    if GroqBrain.parse_minimize(reply):
        actuator.minimize_window()
        hud_emit("SPEAKING", transcript=user_text,
                 reply="Window minimized.", stats=store.stats())
        return True

    if GroqBrain.parse_maximize(reply):
        actuator.maximize_window()
        hud_emit("SPEAKING", transcript=user_text,
                 reply="Window maximized.", stats=store.stats())
        return True

    if GroqBrain.parse_screenshot(reply):
        actuator.take_screenshot(cfg.SCREENSHOT_DIR)
        hud_emit("SPEAKING", transcript=user_text,
                 reply="Screenshot saved.", stats=store.stats())
        return True

    volume_action = GroqBrain.parse_volume(reply)
    if volume_action:
        if volume_action == "up":
            actuator.volume_up()
        elif volume_action == "down":
            actuator.volume_down()
        elif volume_action == "mute":
            actuator.volume_mute()
        hud_emit("SPEAKING", transcript=user_text,
                 reply=f"Volume {volume_action}.", stats=store.stats())
        return True

    # ── Plain spoken reply ────────────────────────────────────────────────
    # Strip any leftover tags before TTS
    clean_reply = re.sub(r"\[.*?\]", "", reply).strip()
    if clean_reply:
        hud_emit("SPEAKING", transcript=user_text,
                 reply=clean_reply, stats=store.stats())
        tts.speak(clean_reply)
    return True


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    wake_fn, stt, tts, brain, actuator, store = boot()
    session_id = store.new_session()
    print(f"  🗝   Session: {session_id[:8]}…\n")

    stats = store.stats()
    stats["session_id"] = session_id
    hud_emit("SLEEPING", stats=stats)

    # ── Wait for wake gesture ─────────────────────────────────────────────
    if wake_fn is not None:
        print("👋  Double-clap to activate Jarvis...")
        wake_fn()
    hud_emit("LISTENING")
    tts.speak("JARVIS online. Scanning technology signals.")
    _speak_technology_briefing(brain, tts, store, session_id)
    tts.speak("Ready when you are.")
    print("\n✅  Session active. Say 'goodbye' to end.\n")

    # ── Continuous listening loop ─────────────────────────────────────────
    while True:
        try:
            print("🎤  Ready...")
            hud_emit("LISTENING", stats=store.stats())
            user_text = stt.listen_and_transcribe()

            if not user_text or len(user_text.strip()) < 3:
                continue   # Silence or noise — stay in listening loop

            should_continue = handle_command(
                user_text, session_id, brain, actuator, tts, store
            )

            if not should_continue:
                final = "Powering down. Stay sharp."
                hud_emit("SLEEPING", transcript="", reply=final, stats=store.stats())
                tts.speak(final)
                break

        except KeyboardInterrupt:
            print("\n\n  [Ctrl-C detected]")
            hud_emit("SLEEPING", reply="Jarvis shutting down.")
            tts.speak("Shutting down. Goodbye.")
            break

        except Exception as exc:
            print(f"\n  [ERROR] {exc}")
            hud_emit("SLEEPING", reply=f"Error: {exc}")
            tts.speak("I encountered an error. Resetting.")
            # Don't crash — recover and keep listening

    # ── Graceful shutdown ─────────────────────────────────────────────────
    actuator.cancel_all_reminders()
    if _vision is not None:
        _vision.stop_capture()
    if _bridge is not None:
        try:
            _bridge.stop()
        except Exception:
            pass
    tts.shutdown()
    store.close()
    print("\nJ.A.R.V.I.S. powered down gracefully.\n")


if __name__ == "__main__":
    main()
