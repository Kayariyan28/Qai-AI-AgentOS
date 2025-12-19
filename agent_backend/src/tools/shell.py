import subprocess
from langchain.tools import tool

ALLOWED_COMMANDS = {"ls", "pwd", "whoami", "df", "free", "mkdir", "touch", "echo", "cat", "grep", "date", "uname"}

@tool
def safe_shell_execute(command: str) -> str:
    """Execute a safe shell command and return its output. Only allowed commands are permitted."""
    cmd_parts = command.split()
    if not cmd_parts or cmd_parts[0] not in ALLOWED_COMMANDS:
        return f"Error: Command '{cmd_parts[0] if cmd_parts else ''}' not allowed for security reasons. Allowed: {', '.join(ALLOWED_COMMANDS)}"
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True, timeout=30)
        return result.stdout.strip() if result.stdout else "Command executed successfully."
    except subprocess.CalledProcessError as e:
        return f"Error executing command: {e.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out."
