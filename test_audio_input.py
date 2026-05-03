#!/usr/bin/env python3
"""
test_audio_input.py
══════════════════
Test script to verify audio input is working for wake word detection.

Usage:
    python test_audio_input.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'jarvis'))

import numpy as np
import sounddevice as sd
import webrtcvad

SAMPLE_RATE = 16_000
FRAME_MS = 20
FRAME_SIZE = int(SAMPLE_RATE * FRAME_MS / 1000)

def test_microphone():
    """Test that microphone is working and can detect speech."""
    print("🎤 Testing microphone input...")
    print("   Speak for 3 seconds when you see 'Recording...'")
    
    try:
        vad = webrtcvad.Vad(1)  # Less aggressive
        frames = []
        speech_detected = False
        
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=FRAME_SIZE,
        ) as stream:
            print("🔴 Recording for 3 seconds...")
            for i in range(150):  # 3 seconds
                chunk, _ = stream.read(FRAME_SIZE)
                frames.append(chunk)
                
                try:
                    is_speech = vad.is_speech(chunk.tobytes(), SAMPLE_RATE)
                    if is_speech:
                        speech_detected = True
                        print("🗣️  Speech detected!", end="\r")
                except Exception:
                    pass
        
        print("\n✅ Recording complete!")
        
        if speech_detected:
            print("🎉 Speech was detected in the recording")
            
            # Save a small sample for debugging
            audio = np.concatenate(frames).astype(np.float32) / 32768.0
            import soundfile as sf
            sf.write("test_recording.wav", audio, SAMPLE_RATE)
            print("💾 Sample saved as 'test_recording.wav'")
            
            return True
        else:
            print("⚠️  No speech detected - try speaking louder or closer to mic")
            return False
            
    except Exception as e:
        print(f"❌ Error testing microphone: {e}")
        return False

def test_whisper_transcription():
    """Test Whisper transcription on the recorded audio."""
    try:
        from faster_whisper import WhisperModel
        
        print("🧠 Testing Whisper transcription...")
        model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
        
        if os.path.exists("test_recording.wav"):
            segments, _ = model.transcribe("test_recording.wav", beam_size=1)
            text = "".join(s.text for s in segments).strip()
            
            if text:
                print(f"📝 Transcription: '{text}'")
                return True
            else:
                print("⚠️  No transcription - audio might be too quiet")
                return False
        else:
            print("❌ No test recording found")
            return False
            
    except Exception as e:
        print(f"❌ Whisper transcription error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing audio input for wake word detection\n")
    
    mic_ok = test_microphone()
    
    if mic_ok:
        whisper_ok = test_whisper_transcription()
        
        if whisper_ok:
            print("\n🎉 Audio system is working!")
            print("   Your voice wake detector should work properly now.")
        else:
            print("\n⚠️  Microphone works but Whisper has issues")
            print("   Try speaking more clearly or check audio quality")
    else:
        print("\n❌ Microphone issues detected")
        print("   Check your microphone settings and try again")
        sys.exit(1)
