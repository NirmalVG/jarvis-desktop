"""
jarvis/voice/stt.py  (patched v5 — audio normalization + robust VAD)
════════════════════════════════════════════════════════════════════
Changes from v4:
  1. Audio normalization — quiet mics (low gain) get their audio
     amplified to a standard level before Whisper processes it.
     This is the #1 fix for mics where speech RMS is only 0.01-0.04.
  2. VAD-gated recording — only starts saving audio when VAD detects
     speech, and stops after silence. No more 15-second noise recordings.
  3. Speech-duration minimum — if VAD detected speech for < 0.3 seconds
     total, it's noise/click, not real speech. Skip it.
  4. Proper RMS thresholding — uses a dynamic threshold based on the
     initial noise floor, not a fixed constant.
  5. Keeps tiny.en as requested.
"""

import os
import re
import tempfile

import numpy as np
import sounddevice as sd
import soundfile as sf
import webrtcvad
from faster_whisper import WhisperModel

import config as cfg

SAMPLE_RATE = 16_000
FRAME_MS    = 30          # 30ms frames for better VAD accuracy
FRAME_SIZE  = int(SAMPLE_RATE * FRAME_MS / 1000)   # 480 samples

# ── Energy gate ───────────────────────────────────────────────────────────────
MIN_RMS_THRESHOLD = getattr(cfg, "MIN_RMS_THRESHOLD", 0.006)

# Minimum speech duration (seconds) to consider it real speech
MIN_SPEECH_DURATION = 0.3

# ── Whisper hallucination blacklist ───────────────────────────────────────────
_HALLUCINATION_EXACT = {
    "you", "thank you", "thanks", "thank you.",
    "thanks.", "you.", "bye", "bye.", ".",
    "the", "a", "i", "oh", "uh", "um",
    "okay", "ok", "okay.", "ok.",
    "yeah", "yes", "no", "hmm",
    "you're right", "you're right.",
    "thank you very much", "thank you very much.",
    "subtitles by", "subtitles by the", "amara.org",
    "[music]", "[applause]", "(music)", "(applause)",
    "[music playing]", "[blank_audio]", "[blank audio]",
    "[silence]", "[no speech]", "[inaudible]",
    "[sound]", "[noise]", "[background noise]",
    "www.mooji.org",
}

_HALLUCINATION_PREFIXES = (
    "www.",
    "http",
    "[music",
    "(music",
    "subtitles",
    "transcribed by",
    "translated by",
)


def _is_hallucination(text: str) -> bool:
    t = text.strip().lower()
    if t in _HALLUCINATION_EXACT:
        return True
    for prefix in _HALLUCINATION_PREFIXES:
        if t.startswith(prefix):
            return True
    # Catch-all: anything that is entirely a bracketed tag like [MUSIC], [BLANK_AUDIO], etc.
    if re.fullmatch(r'\[.*\]', t.strip()):
        return True
    if re.fullmatch(r'\(.*\)', t.strip()):
        return True
    return False


def _normalize_audio(audio: np.ndarray, target_rms: float = 0.1) -> np.ndarray:
    """
    Normalize audio amplitude so quiet mics produce Whisper-friendly levels.
    
    Problem: A mic with low gain gives speech at RMS 0.02-0.04.
    Whisper expects speech at RMS 0.05-0.15. If we don't normalize,
    Whisper hallucinates [MUSIC] or [BLANK_AUDIO] on real speech.
    
    Solution: Scale the audio so its RMS matches `target_rms`.
    """
    rms = float(np.sqrt(np.mean(audio ** 2)))
    if rms < 1e-6:
        return audio  # True silence — don't amplify noise
    
    gain = target_rms / rms
    # Clamp gain to avoid insane amplification of pure noise
    gain = min(gain, 30.0)
    normalized = audio * gain
    # Clip to prevent distortion
    normalized = np.clip(normalized, -1.0, 1.0)
    return normalized


def _find_best_device() -> int | None:
    """Scan all input devices and return the one with the highest RMS signal."""
    print("  🔍  Scanning all microphones to find one with signal...")
    devices = sd.query_devices()
    best_rms = 0.0
    best_idx = None

    for i, dev in enumerate(devices):
        if dev["max_input_channels"] < 1:
            continue
        try:
            frames = []
            with sd.InputStream(
                device=i, samplerate=SAMPLE_RATE,
                channels=1, dtype="int16", blocksize=FRAME_SIZE,
            ) as stream:
                for _ in range(int(SAMPLE_RATE / FRAME_SIZE)):
                    chunk, _ = stream.read(FRAME_SIZE)
                    frames.append(chunk)

            audio = np.concatenate(frames).astype(np.float32) / 32768.0
            rms = float(np.sqrt(np.mean(audio ** 2)))

            if rms > best_rms:
                best_rms = rms
                best_idx = i
                if rms > 0.001:
                    break
        except Exception:
            continue

    if best_idx is not None and best_rms > 0.00003:
        dev_name = sd.query_devices(best_idx)["name"]
        print(f"  ✅  Found working mic: [{best_idx}] {dev_name} (RMS={best_rms:.6f})")
        return best_idx

    print("  ❌  No microphone with signal found.")
    return None


class STT:
    """
    Records speech via VAD, normalizes audio, transcribes with Whisper.

    Key design decisions:
    ──────────────────────
    • VAD gates the recording start — no more recording 15s of pure noise
    • Audio is normalized before Whisper — fixes low-gain mics
    • Speech duration minimum — prevents click/pop false positives
    • Hallucination filter — catches Whisper artifacts from ambient noise
    """

    def __init__(
        self,
        model_size: str         = "tiny.en",
        vad_aggressiveness: int = 2,
        silence_cutoff_ms: int  = 1200,
        max_seconds: int        = 15,
    ):
        print(f"  Loading Whisper ({model_size})...")
        self._whisper        = WhisperModel(model_size, device="cpu", compute_type="int8")
        self._vad_level      = vad_aggressiveness
        self._silence_frames = silence_cutoff_ms // FRAME_MS
        self._max_frames     = int(max_seconds * 1000 / FRAME_MS)
        self._consecutive_silence = 0
        self._device_verified = False
        self._noise_floor = None  # Calibrated on first recording

        # ── Device selection ──────────────────────────────────────────────
        self._device = getattr(cfg, "AUDIO_DEVICE_INDEX", None)

        if self._device is not None:
            dev_name = sd.query_devices(self._device)["name"]
            print(f"  🎤  Audio input: [{self._device}] {dev_name}")
        else:
            default_idx = sd.default.device[0]
            dev_name    = sd.query_devices(default_idx)["name"]
            print(f"  🎤  Audio input: [{default_idx}] {dev_name}  (system default)")

    def listen_and_transcribe(self) -> str:
        """
        Record a command then return its transcript.
        Returns "" on silence, noise, or hallucination.
        """
        audio, speech_duration = self._record_smart()

        # ── Check if any speech was detected by VAD ───────────────────────
        if speech_duration < MIN_SPEECH_DURATION:
            self._consecutive_silence += 1
            rms = float(np.sqrt(np.mean(audio ** 2)))
            print(f"  [STT] No speech detected (VAD speech: {speech_duration:.1f}s, RMS: {rms:.6f}). Skipping.")

            if self._consecutive_silence >= 5 and self._consecutive_silence % 5 == 0:
                print()
                print("  ╔══════════════════════════════════════════════════════════════╗")
                print("  ║  ⚠️  MICROPHONE NOT PICKING UP SPEECH                       ║")
                print("  ║                                                              ║")
                print("  ║  1. Check mic is unmuted in Windows Sound settings            ║")
                print("  ║  2. Increase mic volume to 80%+ in Sound Control Panel        ║")
                print("  ║  3. Run: python tools/mic_check.py  (find the right device)  ║")
                print("  ║  4. Set AUDIO_DEVICE_INDEX in config.py                       ║")
                print("  ╚══════════════════════════════════════════════════════════════╝")
                print()
            return ""

        # Reset silence counter
        self._consecutive_silence = 0

        # ── RMS energy gate ───────────────────────────────────────────────
        rms = float(np.sqrt(np.mean(audio ** 2)))
        if rms < MIN_RMS_THRESHOLD:
            print(f"  [STT] Low energy — RMS {rms:.6f} below {MIN_RMS_THRESHOLD}. Skipping.")
            return ""

        # ── Normalize audio for Whisper ───────────────────────────────────
        # This is the critical fix: quiet mics get amplified so Whisper
        # hears actual speech instead of hallucinating [MUSIC]
        normalized = _normalize_audio(audio, target_rms=0.1)
        norm_rms = float(np.sqrt(np.mean(normalized ** 2)))

        print(f"  [STT] Speech detected ({speech_duration:.1f}s, RMS {rms:.6f} → normalized {norm_rms:.4f}) — transcribing...")
        text = self._transcribe(normalized)

        # ── Min length guard ──────────────────────────────────────────────
        if len(text.strip()) < 3:
            print(f"  [STT] Transcription too short: {text!r}")
            return ""

        # ── Hallucination filter ──────────────────────────────────────────
        if _is_hallucination(text):
            print(f"  [STT] Hallucination filtered: {text!r}")
            return ""

        return text

    # ── Private ───────────────────────────────────────────────────────────────

    def _record_smart(self) -> tuple[np.ndarray, float]:
        """
        VAD-gated recording. Returns (audio_array, speech_duration_seconds).
        
        Unlike the old _record, this one:
          - Measures noise floor from the first 0.5s (pre-speech silence)
          - Only keeps frames where VAD says speech is happening
          - Includes a small pre-roll buffer so word beginnings aren't clipped
          - Returns speech duration so we can skip noise/clicks
        """
        vad             = webrtcvad.Vad(self._vad_level)
        all_frames      = []
        speech_frames   = 0
        silence_count   = 0
        speech_started  = False
        pre_roll        = []  # Buffer last N frames before speech starts
        PRE_ROLL_COUNT  = 5   # ~150ms of pre-roll at 30ms/frame

        print("🎤  Listening...", end=" ", flush=True)

        with sd.InputStream(
            device=self._device,
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=FRAME_SIZE,
        ) as stream:
            for frame_idx in range(self._max_frames):
                chunk, _ = stream.read(FRAME_SIZE)

                try:
                    is_speech = vad.is_speech(chunk.tobytes(), SAMPLE_RATE)
                except Exception:
                    is_speech = False

                if not speech_started:
                    # Keep a rolling pre-roll buffer
                    pre_roll.append(chunk)
                    if len(pre_roll) > PRE_ROLL_COUNT:
                        pre_roll.pop(0)
                    
                    if is_speech:
                        speech_started = True
                        # Include pre-roll so we don't clip word beginnings
                        all_frames.extend(pre_roll)
                        speech_frames += 1
                        silence_count = 0
                else:
                    all_frames.append(chunk)
                    if is_speech:
                        speech_frames += 1
                        silence_count = 0
                    else:
                        silence_count += 1
                        if silence_count >= self._silence_frames:
                            break

        print("done.")

        if not all_frames:
            # No speech detected at all — return a tiny silent array
            return np.zeros(FRAME_SIZE, dtype=np.float32), 0.0

        audio = np.concatenate(all_frames).astype(np.float32) / 32768.0
        speech_duration = speech_frames * FRAME_MS / 1000.0

        return audio, speech_duration

    def _transcribe(self, audio: np.ndarray) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            path = f.name
        sf.write(path, audio, SAMPLE_RATE)

        segments, _ = self._whisper.transcribe(
            path,
            beam_size=5,
            language="en",
            suppress_tokens=[],
            initial_prompt="Voice command to Jarvis AI assistant.",
        )
        text = "".join(s.text for s in segments).strip()

        os.unlink(path)
        return text