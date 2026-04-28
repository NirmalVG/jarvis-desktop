"""
jarvis/wake/keyword_detector.py
════════════════════════════════
Keyword wake word detector using openwakeword — free, offline, no API key.

openwakeword ships with pre-trained models. We use "hey_mycroft" as a
stand-in until a custom "hey_jarvis" model is trained (see bottom of file).

The model processes 80ms chunks (1280 samples at 16kHz). A detection fires
when the rolling score exceeds THRESHOLD for a single chunk.

Install: pip install openwakeword
Models download automatically on first run (~few MB).
"""

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16_000
CHUNK_SIZE  = 1_280      # 80ms — recommended by openwakeword docs


class KeywordDetector:
    """
    Blocks until the configured wake word is detected.

    Available built-in models (no download needed):
      "alexa"         — say "Alexa"
      "hey_mycroft"   — say "Hey Mycroft"
      "hey_rhasspy"   — say "Hey Rhasspy"

    For a real "Hey Jarvis" model:
      Option A — Train your own: https://github.com/dscripka/openWakeWord#training
      Option B — Use the clap detector (already built, no words needed)

    Parameters
    ──────────
    model_name  — openwakeword model name or path to custom .onnx file
    threshold   — detection confidence (0.0–1.0); lower = more sensitive
    """

    def __init__(
        self,
        model_name: str  = "hey_mycroft",
        threshold: float = 0.5,
    ):
        from openwakeword.model import Model

        print(f"  Loading openwakeword model: {model_name}...")
        self._oww       = Model(wakeword_models=[model_name], inference_framework="onnx")
        self._threshold = threshold
        self._model_key = model_name   # key used in prediction dict

    def listen(self) -> None:
        """Block until wake word is detected."""
        print(f"💤  Sleeping... trigger the wake word.")
        self._oww.reset()              # Clear any stale state

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=CHUNK_SIZE,
        ) as stream:
            while True:
                chunk, _ = stream.read(CHUNK_SIZE)
                audio     = chunk.flatten().astype(np.float32) / 32768.0

                predictions = self._oww.predict(audio)

                # Check all loaded models (in case model key differs slightly)
                for key, score in predictions.items():
                    if score >= self._threshold:
                        print(f"  ✓ Wake word '{key}' detected (score: {score:.2f}).")
                        self._oww.reset()
                        return


# ── Custom model training notes ───────────────────────────────────────────────
#
# To train a "hey_jarvis" model:
#
# 1. Record ~100 positive samples of yourself saying "Hey Jarvis"
#    (jarvis_1.wav, jarvis_2.wav, ...)
#
# 2. pip install openwakeword[training]
#
# 3. from openwakeword.train import train_model
#    train_model(
#        positive_reference_clips=["jarvis_1.wav", ...],
#        output_dir="./models",
#        model_name="hey_jarvis",
#    )
#
# 4. In config.py:
#    KEYWORD_MODEL = "./models/hey_jarvis.onnx"