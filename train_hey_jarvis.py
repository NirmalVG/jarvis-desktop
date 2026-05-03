#!/usr/bin/env python3
"""
train_hey_jarvis.py
══════════════════
Helper script to train a custom "Hey Jarvis" wake word model.

This script uses openWakeWord to train a custom model from your voice recordings.

Usage:
1. Record ~100 samples of yourself saying "Hey Jarvis" as WAV files
2. Place them in a directory (e.g., "hey_jarvis_samples/")
3. Run this script: python train_hey_jarvis.py

Requirements:
    pip install openwakeword[training]

After training, update config.py:
    KEYWORD_MODEL = "./models/hey_jarvis.onnx"
"""

import os
import sys
from pathlib import Path

def train_model():
    """Train a custom 'Hey Jarvis' model using openWakeWord."""
    
    # Check if openwakeword is available
    try:
        from openwakeword.train import train_model
    except ImportError:
        print("❌ Error: openwakeword[training] not installed")
        print("   Run: pip install openwakeword[training]")
        return False
    
    # Sample directory
    samples_dir = Path("hey_jarvis_samples")
    if not samples_dir.exists():
        print(f"❌ Error: Samples directory '{samples_dir}' not found")
        print("   Create it and add ~100 WAV files of you saying 'Hey Jarvis'")
        return False
    
    # Find all WAV files in the samples directory
    wav_files = list(samples_dir.glob("*.wav"))
    if len(wav_files) < 10:
        print(f"❌ Error: Found only {len(wav_files)} WAV files")
        print("   Add at least 10-100 WAV files of you saying 'Hey Jarvis'")
        return False
    
    print(f"🎤 Found {len(wav_files)} WAV files for training")
    
    # Create models directory if it doesn't exist
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    try:
        print("🚀 Starting training...")
        print("   This may take 10-30 minutes depending on your CPU...")
        
        # Train the model
        train_model(
            positive_reference_clips=[str(f) for f in wav_files],
            output_dir=str(models_dir),
            model_name="hey_jarvis",
        )
        
        print(f"✅ Training completed!")
        print(f"   Model saved to: {models_dir}/hey_jarvis.onnx")
        print("\n📝 Next steps:")
        print("   1. Update config.py:")
        print("      KEYWORD_MODEL = './models/hey_jarvis.onnx'")
        print("   2. Restart Jarvis")
        print("   3. Say 'Hey Jarvis' to wake it up!")
        
        return True
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        return False

def create_sample_recording_script():
    """Create a helper script to record samples."""
    script_content = '''#!/usr/bin/env python3
"""
record_samples.py
═════════════════
Helper script to record "Hey Jarvis" samples for training.

Usage:
    python record_samples.py
    Speak "Hey Jarvis" when prompted.
    Press Ctrl+C to stop recording.
"""

import sounddevice as sd
import numpy as np
import wavio
import os
import time

SAMPLE_RATE = 16000
DURATION = 2.0  # seconds

def record_sample(filename):
    """Record a single audio sample."""
    print(f"\n🎤 Recording {filename}...")
    print("   Say 'Hey Jarvis' now!")
    
    # Record audio
    audio = sd.rec(int(SAMPLE_RATE * DURATION), 
                   samplerate=SAMPLE_RATE, 
                   channels=1, 
                   dtype='int16')
    sd.wait()  # Wait until recording is finished
    
    # Save to file
    wavio.write(filename, audio, SAMPLE_RATE, sampwidth=2)
    print(f"✅ Saved {filename}")

def main():
    """Record multiple samples."""
    samples_dir = "hey_jarvis_samples"
    os.makedirs(samples_dir, exist_ok=True)
    
    print("🎤 Recording 'Hey Jarvis' samples")
    print("   Press Ctrl+C to stop")
    print("   Try to speak naturally but clearly")
    
    count = 0
    try:
        while True:
            count += 1
            filename = f"{samples_dir}/jarvis_{count:03d}.wav"
            record_sample(filename)
            time.sleep(1)  # Brief pause between recordings
            
    except KeyboardInterrupt:
        print(f"\n✅ Recorded {count} samples")
        print("   Ready for training with: python train_hey_jarvis.py")

if __name__ == "__main__":
    main()
'''
    
    with open("record_samples.py", "w") as f:
        f.write(script_content)
    
    print("📝 Created record_samples.py for recording your voice samples")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--create-recorder":
        create_sample_recording_script()
    else:
        print("🎯 Training 'Hey Jarvis' wake word model")
        print("   Use --create-recorder to make a recording helper script")
        print()
        
        if train_model():
            print("\n🎉 Success! Your custom 'Hey Jarvis' model is ready!")
        else:
            print("\n💡 Tips for better training:")
            print("   - Record 50-100 samples in different environments")
            print("   - Speak naturally but clearly")
            print("   - Vary your distance from the microphone")
            print("   - Include samples with slight background noise")
