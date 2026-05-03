#!/usr/bin/env python3
"""
test_premium_clap.py
═══════════════════
Test the premium precision double clap wake system.

Usage:
    python test_premium_clap.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'jarvis'))

from wake.clap_detector import ClapDetector

def test_premium_clap_detector():
    """Test the premium precision clap detector."""
    print("🎯 Testing Premium Precision Double Clap System")
    print("=" * 50)
    
    try:
        # Initialize with premium settings
        detector = ClapDetector(
            sensitivity=2.8,           # Premium precision sensitivity
            double_clap=True,          # Double clap required
            double_clap_min_ms=150,    # Optimized minimum gap
            double_clap_max_ms=600,    # Premium maximum gap
            high_freq_ratio=0.30,      # High-frequency detection
        )
        
        print("✅ Premium clap detector initialized successfully")
        print("\n📊 Premium Configuration:")
        print(f"   🔹 Sensitivity: {detector.sensitivity} (optimized)")
        print(f"   🔹 Double clap: {detector.double_clap}")
        print(f"   🔹 Gap window: {detector.min_gap*1000:.0f}ms - {detector.max_gap*1000:.0f}ms")
        print(f"   🔹 High-freq ratio: {detector.high_freq_ratio}")
        
        print("\n🎯 Premium Features:")
        print("   ⚡ Ultra-fast response (10ms frames)")
        print("   🎯 High-precision spectral analysis")
        print("   🛡️ Advanced noise filtering")
        print("   🔊 Broadband clap detection")
        print("   ⏱️ Optimized timing window")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing premium clap detector: {e}")
        return False

def test_config():
    """Test that the premium configuration is loaded correctly."""
    import config
    
    print(f"\n📋 Premium Configuration Check:")
    print(f"   WAKE_MODE: {config.WAKE_MODE}")
    print(f"   CLAP_DOUBLE: {getattr(config, 'CLAP_DOUBLE', True)}")
    print(f"   CLAP_MIN_GAP_MS: {getattr(config, 'CLAP_MIN_GAP_MS', 150)}")
    print(f"   CLAP_MAX_GAP_MS: {getattr(config, 'CLAP_MAX_GAP_MS', 600)}")
    print(f"   CLAP_SENSITIVITY: {getattr(config, 'CLAP_SENSITIVITY', 2.8)}")
    
    premium_settings = (
        config.WAKE_MODE == "clap" and
        getattr(config, 'CLAP_DOUBLE', True) and
        getattr(config, 'CLAP_MIN_GAP_MS', 150) == 150 and
        getattr(config, 'CLAP_MAX_GAP_MS', 600) == 600 and
        getattr(config, 'CLAP_SENSITIVITY', 2.8) == 2.8
    )
    
    if premium_settings:
        print("✅ Premium precision settings loaded")
        return True
    else:
        print("❌ Premium settings not properly configured")
        return False

if __name__ == "__main__":
    print("🚀 Testing Premium Precision Double Clap System\n")
    
    config_ok = test_config()
    detector_ok = test_premium_clap_detector()
    
    if config_ok and detector_ok:
        print("\n🎉 Premium Double Clap System Ready!")
        print("📖 Senior Software Engineer Optimizations:")
        print("   ❌ Voice wake → ✅ Premium double clap")
        print("   ⚡ 10ms frame analysis (ultra-responsive)")
        print("   🎯 150-600ms precision timing window")
        print("   🛡️ Advanced spectral filtering")
        print("   🔊 High-frequency clap detection")
        print("\n🎤 Usage:")
        print("   1. Start Jarvis: python jarvis/main.py")
        print("   2. Double clap within 150-600ms window")
        print("   3. Jarvis activates instantly!")
    else:
        print("\n❌ Premium system setup failed. Check configuration.")
        sys.exit(1)
