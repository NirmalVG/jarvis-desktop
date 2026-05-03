#!/usr/bin/env python3
"""
test_voice_wake.py
═════════════════
Test the new voice wake word functionality.

Usage:
    python test_voice_wake.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'jarvis'))

from wake.voice_detector import VoiceDetector

def test_voice_detector():
    """Test that the voice detector can be initialized."""
    print("🎯 Testing voice wake detector...")
    
    try:
        detector = VoiceDetector(wake_phrase="hey jarvis")
        print("✅ Voice detector initialized successfully")
        print("💡 Wake phrase is: 'Hey Jarvis'")
        print("   To test: Run Jarvis and say 'Hey Jarvis' to wake it")
        print("   Press Ctrl+C to stop Jarvis")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing voice detector: {e}")
        print("💡 Make sure the STT dependencies are installed:")
        print("   pip install openai-whisper")
        return False

def test_config():
    """Test that the configuration is loaded correctly."""
    import config
    
    print(f"📋 Configuration check:")
    print(f"   WAKE_MODE: {config.WAKE_MODE}")
    
    if config.WAKE_MODE == "voice":
        print("✅ Wake mode set to voice detection")
        return True
    else:
        print("❌ Wake mode not set to voice")
        return False

if __name__ == "__main__":
    print("🚀 Testing Jarvis voice wake word configuration\n")
    
    config_ok = test_config()
    detector_ok = test_voice_detector()
    
    if config_ok and detector_ok:
        print("\n🎉 All tests passed!")
        print("📖 Summary of changes:")
        print("   ❌ Double clap wake → ✅ Voice wake ('Hey Jarvis')")
        print("   🎤 Start Jarvis: python jarvis/main.py")
        print("   🗣️  Say 'Hey Jarvis' to activate Jarvis")
        print("   ⚡ Uses existing STT system - no extra models needed!")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
        sys.exit(1)
