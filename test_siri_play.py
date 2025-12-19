from agent_backend.src.tools.music_player import play_music

print("Testing Music Player with Siri Integration...")
print("This will attempt to open Spotlight and type 'Play Shape of You by Ed Sheeran'...")

# Test default mode (should prompt library or fail back)
# print("1. Testing default Library mode...")
# result = play_music.invoke({"song": "Shape of You", "artist": "Ed Sheeran"})
# print(f"Result: {result}")

# Test Siri mode (Default now)
print("\n2. Testing Default (Siri) mode...")
result = play_music.invoke({"song": "Shape of You", "artist": "Ed Sheeran"})
print(f"Result: {result}")
