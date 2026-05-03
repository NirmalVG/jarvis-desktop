"""
jarvis/wake/voice_detector.py
═════════════════════════════
Simple voice wake word detector using existing STT system.

This approach uses the existing Whisper STT to listen for "Hey Jarvis"
without requiring additional ML models or dependencies.

Algorithm:
1. Continuously monitor audio with sensitive VAD settings
2. When speech is detected, record a short clip (2-3 seconds)
3. Transcribe with Whisper and check for wake phrase
4. Wake up if detected, otherwise continue listening

This is slower than dedicated wake word models but uses existing infrastructure.
"""

import time
import numpy as np
import sounddevice as sd
import soundfile as sf
import tempfile
import os
from faster_whisper import WhisperModel
import webrtcvad

SAMPLE_RATE = 16_000
FRAME_MS = 20
FRAME_SIZE = int(SAMPLE_RATE * FRAME_MS / 1000)

class VoiceDetector:
    """
    Blocks until "Hey Jarvis" is detected using optimized STT for wake words.
    
    This approach:
    - Uses sensitive VAD settings for wake word detection
    - Short recording windows optimized for wake phrases
    - No additional ML models needed
    - More responsive than the regular STT system
    """
    
    def __init__(self, wake_phrase: str = "hey jarvis", timeout_seconds: int = 30):
        self.wake_phrase = wake_phrase.lower()
        self.timeout_seconds = timeout_seconds
        
        # Initialize Whisper with tiny model for faster processing
        print("  Loading Whisper (tiny.en) for wake detection...")
        self._whisper = WhisperModel("tiny.en", device="cpu", compute_type="int8")
        
        # More sensitive VAD settings for wake word detection
        self._vad_level = 1  # Less aggressive (0-3 scale)
        self._silence_frames = 15  # ~300ms of silence to stop recording
        self._max_frames = 150  # ~3 seconds max recording
        
    def listen(self) -> None:
        """Block until wake phrase is detected."""
        print(f"🎤  Listening for wake phrase: '{self.wake_phrase.title()}'...")
        print("   (Say 'Hey Jarvis' to activate)")
        
        start_time = time.time()
        
        while True:
            try:
                # Check timeout
                if time.time() - start_time > self.timeout_seconds:
                    print(f"   ⏱️  Timeout after {self.timeout_seconds}s, continuing to listen...")
                    start_time = time.time()
                
                # Listen for speech with wake-optimized settings
                transcript = self._listen_and_transcribe_wake()
                
                if transcript and len(transcript.strip()) > 0:
                    print(f"   📝 Heard: \"{transcript}\"")
                    
                    # Check if wake phrase is in the transcript
                    if self.wake_phrase in transcript.lower():
                        print(f"✅ Wake phrase detected!")
                        return
                    else:
                        print("   ❌ Not the wake phrase, continuing...")
                        
            except KeyboardInterrupt:
                print("\n   ⏹️  Wake detection stopped by user")
                raise
            except Exception as e:
                print(f"   ⚠️  Error in wake detection: {e}")
                time.sleep(0.5)  # Brief pause before retrying
    
    def _listen_and_transcribe_wake(self) -> str:
        """Record a short audio clip optimized for wake word detection."""
        vad = webrtcvad.Vad(self._vad_level)
        frames = []
        silence_count = 0
        speech_started = False
        total_frames = 0
        
        print("🎤  Listening...", end=" ", flush=True)
        
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=FRAME_SIZE,
        ) as stream:
            while total_frames < self._max_frames:
                chunk, _ = stream.read(FRAME_SIZE)
                frames.append(chunk)
                total_frames += 1
                
                try:
                    is_speech = vad.is_speech(chunk.tobytes(), SAMPLE_RATE)
                except Exception:
                    is_speech = False
                
                if is_speech:
                    speech_started = True
                    silence_count = 0
                elif speech_started:
                    silence_count += 1
                    if silence_count >= self._silence_frames:
                        break
        
        print("done.")
        
        # Only transcribe if we detected some speech
        if not speech_started:
            return ""
        
        # Convert to float32 and transcribe
        audio = np.concatenate(frames).astype(np.float32) / 32768.0
        return self._transcribe(audio)
    
    def _transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio with Whisper."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            path = f.name
        sf.write(path, audio, SAMPLE_RATE)
        
        try:
            segments, _ = self._whisper.transcribe(path, beam_size=1)
            text = "".join(s.text for s in segments).strip()
        except Exception as e:
            print(f"   ⚠️  Transcription error: {e}")
            text = ""
        finally:
            os.unlink(path)
        
        return text
