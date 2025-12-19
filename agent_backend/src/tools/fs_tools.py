from langchain_core.tools import tool
import os
from typing import List

# Import tools from other modules
from src.tools.shell import safe_shell_execute
from src.tools.web_search import web_search
from src.tools.calculator import calculator
from src.tools.plotter import plot_with_matplotlib
from src.tools.ml_builder import build_ml_models
from src.tools.data_auditor import audit_and_save_data
from src.tools.email_composer import compose_email
from src.tools.music_player import play_music
from src.tools.chess_battle import play_chess_battle
from src.tools.psych_test.orchestrator import run_agent_psych_test

@tool
def list_directory(path: str = ".") -> str:
    """List files and directories in the given path.
    
    Args:
        path: Relative or absolute path to list. Defaults to current directory.
    """
    try:
        items = os.listdir(path)
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {e}"

@tool
def make_directory(path: str) -> str:
    """Create a new directory.
    
    Args:
        path: Path of the directory to create.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return f"Created directory: {path}"
    except Exception as e:
        return f"Error creating directory: {e}"

@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file.
    
    Args:
        path: Path to the file.
        content: String content to write.
    """
    try:
        with open(path, "w") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {e}"

@tool
def read_file(path: str) -> str:
    """Read content from a file.
    
    Args:
        path: Path to the file to read.
    """
    try:
        with open(path, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

# All tools available to the agent
ALL_TOOLS = [
    # File system tools
    list_directory,
    make_directory,
    write_file,
    read_file,
    # Shell execution
    safe_shell_execute,
    # Web search
    web_search,
    # Math
    calculator,
    # Plotting
    plot_with_matplotlib,
    # Machine Learning
    build_ml_models,
    # Data Engineering
    audit_and_save_data,
    # Communication
    compose_email,
    # Entertainment
    play_music,
    # Games
    play_chess_battle,
    # Agent Evaluation
    run_agent_psych_test,
]
