"""
jarvis/tools/mic_check.py
══════════════════════════
Run this directly to diagnose your microphone setup:
  python tools/mic_check.py

It will:
  1. List every audio input device sounddevice can see
  2. Test each input device for 2 seconds and print the RMS
  3. Recommend which device index to set in config.py

Usage after identifying the right device:
  In jarvis/config.py, add:
    AUDIO_DEVICE_INDEX = <number>   # e.g. 2

  In jarvis/voice/stt.py, the patched STT.__init__ reads this.
"""

import sys
import time

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16_000
TEST_SECONDS = 2
FRAME_SIZE = int(SAMPLE_RATE * 0.02)  # 20ms frames


def list_devices():
    print("\n" + "═" * 60)
    print("  AVAILABLE AUDIO INPUT DEVICES")
    print("═" * 60)
    devices = sd.query_devices()
    input_devices = []
    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            mark = "  ←─ DEFAULT" if i == sd.default.device[0] else ""
            print(f"  [{i:2d}] {dev['name'][:45]:<45} ch={dev['max_input_channels']}{mark}")
            input_devices.append(i)
    print("═" * 60)
    return input_devices


def test_device(device_index: int, seconds: float = TEST_SECONDS) -> float:
    """Record `seconds` of audio from `device_index` and return RMS."""
    try:
        dev_info = sd.query_devices(device_index)
        # Use device's native sample rate if it doesn't support 16kHz
        try:
            sd.check_input_settings(device=device_index, samplerate=SAMPLE_RATE, channels=1)
            sr = SAMPLE_RATE
        except Exception:
            sr = int(dev_info["default_samplerate"])

        frames = []
        with sd.InputStream(
            device=device_index,
            samplerate=sr,
            channels=1,
            dtype="int16",
            blocksize=FRAME_SIZE,
        ) as stream:
            n_frames = int(sr * seconds / FRAME_SIZE)
            for _ in range(n_frames):
                chunk, _ = stream.read(FRAME_SIZE)
                frames.append(chunk)

        audio = np.concatenate(frames).astype(np.float32) / 32768.0
        rms = float(np.sqrt(np.mean(audio ** 2)))
        return rms

    except Exception as exc:
        return -1.0  # Device failed to open


def main():
    print("\nJ.A.R.V.I.S. Microphone Diagnostic")
    print("────────────────────────────────────")

    input_devices = list_devices()

    if not input_devices:
        print("\n❌  No input devices found. Check your audio drivers.")
        sys.exit(1)

    print(f"\nDefault input device index: {sd.default.device[0]}")
    print(f"Default output device index: {sd.default.device[1]}")

    print("\n" + "─" * 60)
    print("  TESTING INPUT DEVICES  (speak or make noise during test)")
    print("─" * 60)

    results = []
    for idx in input_devices:
        dev_name = sd.query_devices(idx)["name"][:40]
        print(f"\n  Testing [{idx:2d}] {dev_name}...", end=" ", flush=True)
        print(f"({TEST_SECONDS}s) SPEAK NOW ▶", end=" ", flush=True)

        rms = test_device(idx)

        if rms < 0:
            print("FAILED (could not open)")
        else:
            bar = "█" * min(40, int(rms * 2000))
            level = "🔴 VERY LOW" if rms < 0.001 else \
                    "🟡 LOW"      if rms < 0.005 else \
                    "🟢 GOOD"     if rms < 0.5   else \
                    "🔵 LOUD"
            print(f"RMS={rms:.6f}  {level}  |{bar}|")
            results.append((rms, idx, sd.query_devices(idx)["name"]))

    print("\n" + "═" * 60)
    print("  RECOMMENDATION")
    print("═" * 60)

    if not results:
        print("  ❌  No working input devices found.")
        sys.exit(1)

    # Sort by RMS descending — highest signal = right mic
    results.sort(reverse=True)
    best_rms, best_idx, best_name = results[0]

    if best_rms < 0.001:
        print(f"\n  ⚠️  All devices returned very low signal (best RMS={best_rms:.6f}).")
        print("  Possible causes:")
        print("    1. Microphone muted in Windows Sound settings")
        print("       → Right-click speaker icon → Sound Settings → Input → Unmute")
        print("    2. Microphone access blocked for Python")
        print("       → Windows Settings → Privacy → Microphone → allow desktop apps")
        print("    3. Microphone volume set to 0")
        print("       → Control Panel → Sound → Recording → Properties → Levels → set to 80+")
    else:
        print(f"\n  ✅  Best device: [{best_idx}] {best_name}")
        print(f"      RMS with speech: {best_rms:.6f}")
        print(f"\n  Add to jarvis/config.py:")
        print(f"      AUDIO_DEVICE_INDEX = {best_idx}")

        if best_idx != sd.default.device[0]:
            print(f"\n  Note: This differs from your system default ({sd.default.device[0]}).")
            print(f"  The config.py setting will override it for Jarvis.")

    print("\n" + "═" * 60)


if __name__ == "__main__":
    main()