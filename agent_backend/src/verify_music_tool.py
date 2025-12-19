
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.tools.music_player import play_music

def test_music_tool():
    print("Testing Music Tool...")
    
    # Test 1: Open App (No args)
    print("\n1. Testing 'Open App' (no args)...")
    try:
        result = play_music.invoke({})
        print(f"Result: {result}")
    except Exception as e:
        print(f"FAILED: {e}")

    # Test 2: Play Song
    print("\n2. Testing 'Play Song' (Wait for it)...")
    try:
        # Note: We use a generic search that strictly shouldn't fail if library is empty, 
        # but realistically we just want to see it try to run script or siri.
        # We'll use a dummy song that might trigger fallback or just fail gracefully.
        result = play_music.invoke({"song": "Shape of You", "artist": "Ed Sheeran", "use_siri": False})
        print(f"Result: {result}")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_music_tool()
