from langchain_core.tools import tool
import subprocess
import shlex

@tool("compose_email")
def compose_email(subject: str, body: str, recipient: str) -> str:
    """
    Composes a new email in the macOS Mail app.
    
    Args:
        subject: The subject line of the email.
        body: The main content/body of the email.
        recipient: The email address of the recipient.
    """
    try:
        # Escape quotes for AppleScript
        subject_safe = subject.replace('"', '\\"')
        body_safe = body.replace('"', '\\"')
        recipient_safe = recipient.replace('"', '\\"')
        
        apple_script = f'''
        tell application "Mail"
            set newMessage to make new outgoing message with properties {{subject:"{subject_safe}", content:"{body_safe} & return & return", visible:true}}
            tell newMessage
                make new to recipient at end of to recipients with properties {{address:"{recipient_safe}"}}
            end tell
            activate
        end tell
        '''
        
        # Run AppleScript
        process = subprocess.run(
            ['osascript', '-e', apple_script], 
            capture_output=True, 
            text=True
        )
        
        if process.returncode == 0:
            return f"Successfully opened Mail app with draft to {recipient}."
        else:
            return f"Error opening Mail app: {process.stderr}"

    except Exception as e:
        return f"Error executing email composer: {str(e)}"
