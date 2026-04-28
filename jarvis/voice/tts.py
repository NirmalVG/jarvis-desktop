"""
jarvis/voice/tts.py

Text-to-speech for Jarvis.

Engines:
  system - Windows SAPI speech. Most reliable on Windows.
  auto   - Edge neural TTS first, then local fallback.
  edge   - Edge neural TTS first, then local fallback if it fails.

Edge TTS is nicer when it works, but it can return an empty audio stream on
some networks or package versions. When that happens, Jarvis uses local speech
for that one line and tries the neural voice again on the next line.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import TimeoutError


class TTS:
    """Speak text aloud."""

    def __init__(
        self,
        engine: str = "system",
        voice: str = "en-US-GuyNeural",
        rate: int = 175,
        tts_rate: str = "+0%",
    ):
        self._engine = engine.lower().strip()
        self._voice = voice
        self._rate = rate
        self._tts_rate = tts_rate
        self._pygame = None
        self._fallback = None
        self._edge_available = self._engine in ("auto", "edge")
        self._speak_lock = threading.Lock()

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

        if self._edge_available:
            self._init_pygame()

    def speak(self, text: str) -> None:
        """Speak text. Blocks until audio finishes."""
        print(f"\nJARVIS: {text}")
        with self._speak_lock:
            if self._engine == "system":
                self._speak_fallback(text)
                return

            if not self._edge_available:
                self._speak_fallback(text)
                return

            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._speak_edge(text), self._loop
                )
                future.result(timeout=self._timeout_for(text))
            except TimeoutError:
                future.cancel()
                self._stop_edge_playback()
                print("  [TTS] Edge speech timed out; switching to local speech.")
                self._speak_fallback(text)
            except Exception as exc:
                self._stop_edge_playback()
                print(f"  [TTS] Edge speech failed: {exc}")
                self._speak_fallback(text)

    def set_voice(self, voice_name: str) -> None:
        """Change the Edge TTS voice at runtime."""
        self._voice = voice_name

    def set_rate(self, rate: str) -> None:
        """Change the Edge TTS speed at runtime, e.g. '+20%' or '-10%'."""
        self._tts_rate = rate

    async def _speak_edge(self, text: str) -> None:
        import edge_tts

        communicate = edge_tts.Communicate(
            text,
            voice=self._voice,
            rate=self._tts_rate,
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            path = f.name

        try:
            await communicate.save(path)

            if os.path.getsize(path) == 0:
                raise RuntimeError("Edge TTS produced an empty audio file.")

            pygame = self._pygame
            if pygame is None:
                raise RuntimeError("pygame mixer is not available.")

            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.05)

            try:
                pygame.mixer.music.unload()
            except Exception:
                pass
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    def _speak_fallback(self, text: str) -> None:
        if sys.platform == "win32":
            try:
                self._speak_system_fallback(text)
                return
            except Exception as exc:
                print(f"  [TTS] Windows system speech failed: {exc}")

        try:
            if self._fallback is None:
                import pyttsx3

                self._fallback = pyttsx3.init()
                self._fallback.setProperty("rate", self._rate)
                self._fallback.setProperty("volume", 1.0)
                self._select_male_fallback_voice()
            self._fallback.say(text)
            self._fallback.runAndWait()
        except Exception as exc:
            raise RuntimeError(f"No local TTS engine could speak: {exc}") from exc

    def _speak_system_fallback(self, text: str) -> None:
        """Speak using built-in Windows SAPI."""
        if sys.platform != "win32":
            raise RuntimeError("Windows system speech is only available on Windows.")

        script = (
            "& { param([string]$Text) "
            "$ErrorActionPreference = 'Stop'; "
            "$speaker = New-Object -ComObject SAPI.SpVoice; "
            "$speaker.Rate = 0; "
            "$speaker.Volume = 100; "
            "[void]$speaker.Speak($Text) "
            "}"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", script, text],
            check=True,
            timeout=self._timeout_for(text),
        )

    def _select_male_fallback_voice(self) -> None:
        """Prefer a male offline voice when pyttsx3 is used."""
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
        """Give long briefings enough time to finish speaking."""
        return max(45, min(180, 20 + len(text) // 12))

    def _stop_edge_playback(self) -> None:
        try:
            if self._pygame:
                self._pygame.mixer.music.stop()
        except Exception:
            pass

    def _init_pygame(self) -> None:
        try:
            import pygame

            pygame.mixer.init()
            self._pygame = pygame
        except Exception as exc:
            print(f"  [TTS] pygame audio unavailable: {exc}")

    def shutdown(self) -> None:
        """Cleanly stop audio resources."""
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
