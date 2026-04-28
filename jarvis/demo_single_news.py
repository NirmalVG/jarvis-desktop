#!/usr/bin/env python3
"""
Demo of the single headline news experience after clap wake.
"""

import sys
sys.path.append('.')

from services.web_search import get_single_global_headline, create_single_headline_briefing
from brain.groq_brain import GroqBrain
from memory.store import MemoryStore
import config as cfg

def demo_clap_wake_news():
    print("👏 Double clap detected...")
    print("🤖 JARVIS activating...")
    print()
    
    print("🔍 Scanning for major global technology developments...")
    
    try:
        # Get the single most important global headline
        headline = get_single_global_headline()
        
        if headline:
            print(f"✅ Found major story: {headline.title[:60]}...")
            print()
            
            # Simulate Jarvis speaking the briefing
            if cfg.GROQ_API_KEY:
                brain = GroqBrain(cfg.GROQ_API_KEY, MemoryStore())
                store = MemoryStore()
                session_id = store.new_session()
                
                briefing = create_single_headline_briefing(headline, brain, store, session_id)
            else:
                briefing = f"The main technology story today: {headline.title} from {headline.source}."
            
            print("🎙️  JARVIS speaks:")
            print(f"   \"{briefing}\"")
            print()
            print("✨ Briefing complete. Ready for your commands.")
            
        else:
            print("⚠️ No major technology developments found at the moment.")
            print("🤖 JARVIS: Ready to assist you.")
            
    except Exception as e:
        error_msg = str(e).lower()
        if "timeout" in error_msg:
            print("⏰ The news servers are responding slowly at the moment.")
        else:
            print(f"❌ Network issue: {e}")
        print("🤖 JARVIS: Ready to assist you.")
    
    print()
    print("🎤 Listening for your commands...")

if __name__ == "__main__":
    demo_clap_wake_news()
