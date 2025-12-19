from langchain_core.tools import tool
import subprocess
import shlex

from typing import Optional

@tool("play_music")
def play_music(song: Optional[str] = None, artist: Optional[str] = None, use_siri: bool = False) -> str:
    """
    Control macOS Music app.
    
    Args:
        song: (Optional) The name of the song/track to play. If omitted, just opens the Music app.
        artist: (Optional) The name of the artist.
        use_siri: (Optional) If True, forces the use of Siri/Spotlight to handle the request.
    """
    import time
    try:
        # Define Spotlight/Siri fallback logic as a reusable block or inline
        def run_siri_spotlight(query_text):
                 spotlight_script = f'''
                 tell application "System Events"
                     -- 1. Activate Spotlight (Cmd + Space)
                     -- Note: key code 49 is Space.
                     key code 49 using command down
                     
                     delay 1.0
                     
                     -- 2. Type the Natural Language Command (Siri-style)
                     keystroke "{query_text}"
                     
                     delay 1.0
                     
                     -- 3. Execute (Enter)
                     keystroke return
                 end tell
                 '''
                 subprocess.run(['osascript', '-e', spotlight_script], capture_output=True, text=True)
                 return f"Sent command to Spotlight/Siri: '{query_text}'."

        # 1. Force Open Music App (Reliable)
        subprocess.run(["open", "-a", "Music"])
        
        # If no song specified, we are done
        if not song:
            return "Opened Apple Music app."

        time.sleep(1) # Wait for launch if it wasn't open
        
        # Normalize artist to empty string if None
        artist = artist or ""
        
        if use_siri:
            query = f"Play {song}"
            if artist:
                query += f" by {artist}"
            return run_siri_spotlight(query)
            
        # 2. Escape quotes
        song_safe = song.replace('"', '\\"')
        artist_safe = artist.replace('"', '\\"')
        
        # 3. Construct Script
        if artist:
            # Proper filter syntax for AppleScript
            apple_script = f'''
            tell application "Music"
                try
                    set trackToPlay to (first track whose name is "{song_safe}" and artist is "{artist_safe}")
                    play trackToPlay
                    return "Success"
                on error
                    return "Error: Track not found"
                end try
            end tell
            '''
        else:
            apple_script = f'''
            tell application "Music"
                try
                    play track "{song_safe}"
                    return "Success"
                on error
                    return "Error: Track not found"
                end try
            end tell
            '''
        
        # 4. Run Script
        process = subprocess.run(
            ['osascript', '-e', apple_script], 
            capture_output=True, 
            text=True
        )
        
        # 5. Logic: If success, done. If ANY error (library missing OR syntax error), fall back to Search.
        output = process.stdout.strip()
        
        if process.returncode == 0 and "Success" in output:
             if artist:
                 return f"Playing '{song}' by '{artist}' from Library."
             else:
                 return f"Playing '{song}' from Library."
        else:
                 # Local Play Failed -> Fallback: "Ask Siri" (via Spotlight)
                 # Spotlight handles natural language queries like "Play X by Y" exactly like Siri.
                 
                 query = f"Play {song} {artist}".strip()
                 return run_siri_spotlight(query)

    except Exception as e:
        return f"Error executing music player: {str(e)}"
