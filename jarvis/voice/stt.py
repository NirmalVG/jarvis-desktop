"""
jarvis/voice/stt.py
═══════════════════
Speech-to-Text: WebRTC VAD for smart recording + faster-whisper for transcription.
"""

import os
import tempfile

import numpy as np
import sounddevice as sd
import soundfile as sf
import webrtcvad
from faster_whisper import WhisperModel

SAMPLE_RATE = 16_000
FRAME_MS    = 20  # Reduced for faster response
FRAME_SIZE  = int(SAMPLE_RATE * FRAME_MS / 1000)   # 480 samples


class STT:
    """
    Records until silence (VAD), then transcribes with Whisper.

    Parameters
    ──────────
    model_size         — "tiny.en", "base.en", "small.en" (base.en recommended)
    vad_aggressiveness — 0-3; higher = cuts more background noise
    silence_cutoff_ms  — ms of silence to stop recording
    max_seconds        — hard ceiling on recording length
    """

    def __init__(
        self,
        model_size: str      = "base.en",
        vad_aggressiveness: int = 2,
        silence_cutoff_ms: int  = 700,
        max_seconds: int         = 9,
    ):
        print(f"  Loading Whisper ({model_size})...")
        self._whisper    = WhisperModel(model_size, device="cpu", compute_type="int8")
        self._vad_level  = vad_aggressiveness
        self._silence_frames = silence_cutoff_ms // FRAME_MS
        self._max_frames = int(max_seconds * 1000 / FRAME_MS)

    def listen_and_transcribe(self) -> str:
        """Record a command then return its transcript. Blocks until done."""
        audio = self._record()
        return self._transcribe(audio)

    # ── Private ───────────────────────────────────────────────────────────────

    def _record(self) -> np.ndarray:
        vad            = webrtcvad.Vad(self._vad_level)
        frames: list   = []
        silence_count  = 0
        speech_started = False

        print("🎤  Listening...", end=" ", flush=True)

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=FRAME_SIZE,
        ) as stream:
            for _ in range(self._max_frames):
                chunk, _ = stream.read(FRAME_SIZE)
                frames.append(chunk)

                try:
                    is_speech = vad.is_speech(chunk.tobytes(), SAMPLE_RATE)
                except Exception:
                    is_speech = False

                if is_speech:
                    speech_started = True
                    silence_count  = 0
                elif speech_started:
                    silence_count += 1
                    if silence_count >= self._silence_frames:
                        break

        print("done.")
        return np.concatenate(frames).astype(np.float32) / 32768.0

    def _transcribe(self, audio: np.ndarray) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            path = f.name
        sf.write(path, audio, SAMPLE_RATE)

        segments, _ = self._whisper.transcribe(path, beam_size=5)
        text = "".join(s.text for s in segments).strip()

        os.unlink(path)
        return text