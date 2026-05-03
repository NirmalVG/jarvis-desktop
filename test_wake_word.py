#!/usr/bin/env python3
"""
test_wake_word.py
═════════════════
Quick test script to verify the wake word functionality works.

Usage:
    python test_wake_word.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'jarvis'))

from wake.keyword_detector import KeywordDetector

def test_keyword_detector():
    """Test that the keyword detector can be initialized."""
    print("🎯 Testing keyword detector...")
    
    try:
        detector = KeywordDetector(model_name='hey_mycroft', threshold=0.5)
        print("✅ Keyword detector initialized successfully")
        print("💡 Wake word is now: 'Hey Mycroft'")
        print("   To test: Run Jarvis and say 'Hey Mycroft' to wake it")
        print("   Press Ctrl+C to stop Jarvis")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing detector: {e}")
        print("💡 Make sure openwakeword is installed:")
        print("   pip install openwakeword")
        return False

def test_config():
    """Test that the configuration is loaded correctly."""
    import config
    
    print(f"📋 Configuration check:")
    print(f"   WAKE_MODE: {config.WAKE_MODE}")
    print(f"   KEYWORD_MODEL: {config.KEYWORD_MODEL}")
    print(f"   KEYWORD_THRESHOLD: {config.KEYWORD_THRESHOLD}")
    
    if config.WAKE_MODE == "keyword":
        print("✅ Wake mode set to keyword detection")
        return True
    else:
        print("❌ Wake mode not set to keyword")
        return False

if __name__ == "__main__":
    print("🚀 Testing Jarvis wake word configuration\n")
    
    config_ok = test_config()
    detector_ok = test_keyword_detector()
    
    if config_ok and detector_ok:
        print("\n🎉 All tests passed!")
        print("📖 Summary of changes:")
        print("   ❌ Double clap wake → ✅ Voice wake ('Hey Mycroft')")
        print("   💡 To use 'Hey Jarvis': run python train_hey_jarvis.py")
        print("   🎤 Start Jarvis: python main.py")
        print("   🗣️  Say 'Hey Mycroft' to activate Jarvis")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
        sys.exit(1)
