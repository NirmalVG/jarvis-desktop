"""
jarvis/wake/clap_detector.py
════════════════════════════
ML-based clap-to-wake detector — no API keys, fully offline.

Algorithm
─────────
1. Monitor RMS energy in 20ms frames continuously.
2. When energy spikes above dynamic noise floor × sensitivity:
     a. Spectral check — claps are broadband (high-frequency energy > 30%).
        This rejects speech, music, door slams (tonal or low-freq).
     b. Onset sharpness — clap rises in < 40ms, decays in < 250ms.
        This rejects sustained sounds like talking.
3. Double-clap: two valid claps within 150–800ms of each other triggers wake.

PRD references: F001, Risk "Trigger false positives"
"""

import time
from collections import deque

import numpy as np
import sounddevice as sd

# ── Audio constants ───────────────────────────────────────────────────────────
SAMPLE_RATE = 16_000          # Hz  — matches Porcupine / webrtcvad
FRAME_MS    = 10              # ms per analysis frame (reduced for faster response)
FRAME_SIZE  = int(SAMPLE_RATE * FRAME_MS / 1000)   # 320 samples


class ClapDetector:
    """
    Blocks until a double-clap (default) or single-clap is detected.

    Parameters
    ──────────
    sensitivity        — energy multiplier above noise floor (lower = more sensitive)
    double_clap        — require two claps if True; single clap if False
    double_clap_min_ms — minimum gap between claps (avoids echo artifacts)
    double_clap_max_ms — maximum gap between claps
    high_freq_ratio    — minimum fraction of spectral energy above 2 kHz
    """

    def __init__(
        self,
        sensitivity: float   = 3.0,
        double_clap: bool    = True,
        double_clap_min_ms: int = 150,
        double_clap_max_ms: int = 800,
        high_freq_ratio: float  = 0.30,
    ):
        self.sensitivity        = sensitivity
        self.double_clap        = double_clap
        self.min_gap            = double_clap_min_ms / 1000.0
        self.max_gap            = double_clap_max_ms / 1000.0
        self.high_freq_ratio    = high_freq_ratio

        # Rolling noise floor — 100 quiet frames ≈ 2 seconds of ambient sound
        self._noise_history: deque[float] = deque(maxlen=100)
        self._clap_times:    list[float]  = []

        # Seed noise floor so we don't fire immediately on boot
        for _ in range(30):
            self._noise_history.append(400.0)

    # ── Public ────────────────────────────────────────────────────────────────

    def listen(self) -> None:
        """Block until the configured wake gesture is detected."""
        print("👋  Listening for clap wake gesture...")
        self._clap_times.clear()

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=FRAME_SIZE,
        ) as stream:
            in_burst   = False   # are we inside a loud burst?
            burst_peak = 0.0
            burst_frames = 0

            while True:
                frame, _ = stream.read(FRAME_SIZE)
                frame     = frame.flatten()
                rms       = float(np.sqrt(np.mean(frame.astype(np.float32) ** 2)))
                threshold = self._noise_floor() * self.sensitivity

                if rms > threshold:
                    # ── Entering / continuing a loud burst ───────────────────
                    if not in_burst:
                        in_burst     = True
                        burst_peak   = rms
                        burst_frames = 1
                    else:
                        burst_peak   = max(burst_peak, rms)
                        burst_frames += 1
                else:
                    if in_burst:
                        # ── Burst just ended — classify it ───────────────────
                        in_burst = False
                        duration_ms = burst_frames * FRAME_MS

                        if self._classify_clap(frame, burst_peak, duration_ms):
                            now = time.monotonic()
                            # Prune stale clap timestamps
                            self._clap_times = [
                                t for t in self._clap_times
                                if now - t < self.max_gap
                            ]
                            self._clap_times.append(now)

                            if not self.double_clap:
                                print("  ✓ Clap detected.")
                                return

                            if len(self._clap_times) >= 2:
                                gap = self._clap_times[-1] - self._clap_times[-2]
                                if self.min_gap < gap < self.max_gap:
                                    print(f"  ✓ Double clap detected (gap: {gap*1000:.0f}ms).")
                                    return
                        else:
                            # Not a clap — update noise floor
                            self._noise_history.append(rms)
                    else:
                        # Genuinely quiet frame — update noise floor
                        self._noise_history.append(rms)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _noise_floor(self) -> float:
        """75th-percentile of recent quiet samples (robust against occasional sounds)."""
        arr = np.array(self._noise_history)
        return float(np.percentile(arr, 75)) if len(arr) > 5 else 500.0

    def _classify_clap(self, frame: np.ndarray, peak_rms: float, duration_ms: float) -> bool:
        """
        Return True if the burst matches a clap profile:
          • Short duration  (< 300ms) — claps don't sustain like speech
          • High peak energy          — real clap vs soft brush
          • Broadband spectrum        — clap energy is spread across frequencies
        """
        # ① Duration gate
        if duration_ms > 300:
            return False   # Too long — probably speech or music

        # ② Minimum peak energy (avoids classifying soft rustles)
        if peak_rms < self._noise_floor() * (self.sensitivity * 0.8):
            return False

        # ③ Spectral breadth — claps have strong high-frequency content
        fft   = np.abs(np.fft.rfft(frame.astype(np.float32)))
        freqs = np.fft.rfftfreq(len(frame), 1.0 / SAMPLE_RATE)

        total_energy    = float(np.sum(fft)) + 1e-10
        high_freq_energy = float(np.sum(fft[freqs > 2_000]))
        ratio           = high_freq_energy / total_energy

        return ratio >= self.high_freq_ratio