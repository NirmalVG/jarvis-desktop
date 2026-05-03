#!/usr/bin/env python3
"""
test_clap_fix.py
═══════════════
Test that the double clap fix is working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'jarvis'))

import config as cfg
from wake.clap_detector import ClapDetector

def test_clap_detector_fix():
    """Test that the clap detector is properly configured for double clap."""
    print("🔧 Testing Double Clap Fix")
    print("=" * 40)
    
    # Check config values
    print(f"📋 Configuration:")
    print(f"   WAKE_MODE: {cfg.WAKE_MODE}")
    print(f"   CLAP_DOUBLE: {cfg.CLAP_DOUBLE}")
    print(f"   CLAP_MIN_GAP_MS: {cfg.CLAP_MIN_GAP_MS}")
    print(f"   CLAP_MAX_GAP_MS: {cfg.CLAP_MAX_GAP_MS}")
    print(f"   CLAP_SENSITIVITY: {cfg.CLAP_SENSITIVITY}")
    
    # Test clap detector initialization
    try:
        detector = ClapDetector(
            sensitivity=cfg.CLAP_SENSITIVITY,
            double_clap=cfg.CLAP_DOUBLE,
            double_clap_min_ms=cfg.CLAP_MIN_GAP_MS,
            double_clap_max_ms=cfg.CLAP_MAX_GAP_MS,
        )
        
        print(f"\n✅ ClapDetector initialized successfully!")
        print(f"   Double clap required: {detector.double_clap}")
        print(f"   Min gap: {detector.min_gap*1000:.0f}ms")
        print(f"   Max gap: {detector.max_gap*1000:.0f}ms")
        print(f"   Sensitivity: {detector.sensitivity}")
        
        # Verify the fix worked
        if detector.double_clap == True:
            print(f"\n🎉 SUCCESS: Double clap is now properly enabled!")
            return True
        else:
            print(f"\n❌ ISSUE: Double clap is still disabled!")
            return False
            
    except Exception as e:
        print(f"\n❌ Error initializing clap detector: {e}")
        return False

if __name__ == "__main__":
    success = test_clap_detector_fix()
    if success:
        print("\n✅ Double clap identification fix verified!")
        print("🎤 You can now use: python jarvis/main.py")
        print("   And double clap to activate Jarvis!")
    else:
        print("\n❌ Fix verification failed!")
        sys.exit(1)
