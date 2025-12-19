import subprocess
import time

print("Opening Music App...")
subprocess.run(["open", "-a", "Music"])
time.sleep(3)

item_dump_script = '''
tell application "System Events"
    tell application process "Music"
        set frontmost to true
        try
            set windowName to name of window 1
            log "Window: " & windowName
            
            tell window 1
                -- Search and Click "Play"
                log "--- Searching for Play Button ---"
                set foundPlay to false
                tell splitter group 1
                    repeat with g in UI elements
                        if (class of g is group) then
                             repeat with b in UI elements of g
                                 if (class of b is button) then
                                     if (description of b is "play") or (description of b is "Play") then
                                         log "FOUND PLAY BUTTON! Clicking..."
                                         click b
                                         set foundPlay to true
                                         return -- Exit after clicking
                                     end if
                                 end if
                             end repeat
                        end if
                    end repeat
                end tell
                
                if foundPlay is false then
                    log "Could not find Play button by description traversal."
                end if
            end tell
        on error e
            log "Error dumping UI: " & e
        end try
    end tell
end tell
'''

print("Dumping UI Elements...")
process = subprocess.run(['osascript', '-e', item_dump_script], capture_output=True, text=True)
print(process.stderr) # 'log' outputs to stderr in osascript
print("Done.")
