"""
jarvis/voice/tts.py
═══════════════════
Text-to-Speech: Microsoft Edge Neural TTS (online) with pyttsx3 offline fallback.

Uses a persistent asyncio event loop in a background thread to avoid conflicts
with the HUD bridge's own asyncio loop. Previous design called asyncio.run()
per speak() invocation which breaks in Python 3.12+ and conflicts with other loops.
"""

import asyncio
import os
import tempfile
import threading
from concurrent.futures import TimeoutError


class TTS:
    """
    Speaks text aloud.

    Tries edge-tts first (natural Neural voice, requires internet).
    Falls back to pyttsx3 if edge-tts fails or internet is unavailable.

    Parameters
    ──────────
    voice      — Edge TTS voice name (en-US-GuyNeural, DavisNeural, TonyNeural…)
    rate       — pyttsx3 fallback speaking rate (WPM)
    tts_rate   — Edge TTS speed adjustment ("+0%", "-20%", "+30%")
    """

    def __init__(self, voice: str = "en-US-GuyNeural", rate: int = 175,
                 tts_rate: str = "+0%"):
        self._voice    = voice
        self._rate     = rate
        self._tts_rate = tts_rate
        self._pygame   = None
        self._fallback = None
        self._speak_lock = threading.Lock()

        # Persistent asyncio loop for edge-tts (avoids asyncio.run() conflicts)
        self._loop     = asyncio.new_event_loop()
        self._thread   = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

        self._init_pygame()

    def speak(self, text: str) -> None:
        """Speak text. Blocks until audio finishes."""
        print(f"\n🤖  JARVIS: {text}")
        with self._speak_lock:
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._speak_edge(text), self._loop
                )
                future.result(timeout=self._timeout_for(text))
            except TimeoutError:
                future.cancel()
                self._stop_edge_playback()
                print("  [TTS] Edge speech timed out; stopped playback instead of starting a second voice.")
            except Exception:
                self._stop_edge_playback()
                self._speak_fallback(text)

    def set_voice(self, voice_name: str) -> None:
        """Change the Edge TTS voice at runtime."""
        self._voice = voice_name

    def set_rate(self, rate: str) -> None:
        """Change the Edge TTS speed at runtime (e.g. '+20%', '-10%')."""
        self._tts_rate = rate

    # ── Edge TTS (primary) ────────────────────────────────────────────────────

    async def _speak_edge(self, text: str) -> None:
        import edge_tts
        communicate = edge_tts.Communicate(
            text, voice=self._voice, rate=self._tts_rate
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            path = f.name
        await communicate.save(path)

        pygame = self._pygame
        if pygame is None:
            os.unlink(path)
            raise RuntimeError("pygame not available")

        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            await asyncio.sleep(0.05)

        try:
            pygame.mixer.music.unload()
        except Exception:
            pass   # Some pygame versions don't have unload()

        os.unlink(path)

    # ── pyttsx3 fallback (offline) ────────────────────────────────────────────

    def _speak_fallback(self, text: str) -> None:
        if self._fallback is None:
            import pyttsx3
            self._fallback = pyttsx3.init()
            self._fallback.setProperty("rate",   self._rate)
            self._fallback.setProperty("volume", 1.0)
            self._select_male_fallback_voice()
        self._fallback.say(text)
        self._fallback.runAndWait()

    def _select_male_fallback_voice(self) -> None:
        """Prefer a male offline voice so fallback never sounds like another speaker."""
        try:
            voices = self._fallback.getProperty("voices") or []
            preferred = None
            for voice in voices:
                blob = " ".join(
                    str(x).lower()
                    for x in (voice.id, voice.name, getattr(voice, "gender", ""))
                    if x
                )
                if any(name in blob for name in ("david", "mark", "george", "male")):
                    preferred = voice
                    break
            if preferred:
                self._fallback.setProperty("voice", preferred.id)
        except Exception:
            pass

    def _timeout_for(self, text: str) -> int:
        """Give long briefings enough time so fallback does not overlap Edge TTS."""
        return max(45, min(180, 20 + len(text) // 12))

    def _stop_edge_playback(self) -> None:
        try:
            if self._pygame:
                self._pygame.mixer.music.stop()
        except Exception:
            pass

    # ── Init ──────────────────────────────────────────────────────────────────

    def _init_pygame(self) -> None:
        try:
            import pygame
            pygame.mixer.init()
            self._pygame = pygame
        except Exception:
            pass   # Will fall back to pyttsx3 at speak time

    # ── Shutdown ──────────────────────────────────────────────────────────────

    def shutdown(self) -> None:
        """Cleanly stop the asyncio loop and release resources."""
        try:
            if self._pygame:
                self._pygame.mixer.quit()
        except Exception:
            pass
        try:
            self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=2)
        except Exception:
            pass
        try:
            if self._fallback:
                self._fallback.stop()
        except Exception:
            pass
