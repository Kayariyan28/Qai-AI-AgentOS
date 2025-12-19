from langchain.tools import tool
import numpy as np
import re
import json

@tool
def plot_with_matplotlib(instructions: str) -> str:
    """Generate a GUI plot. Use Fn+Up/Fn+Down to scroll in QEMU."""
    try:
        # Flexible parsing - clean up whitespace
        text = re.sub(r'\s+', ' ', instructions.strip())
        
        # Remove common prefixes
        text = re.sub(r'^(plot|graph|draw)\s+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^y\s*=\s*', '', text, flags=re.IGNORECASE)
        
        # Now text should be like "sin(x) from 0 to 6" or just "sin(x)"
        if " from " in text.lower():
            idx = text.lower().index(" from ")
            func_str = text[:idx].strip()
            range_str = text[idx+6:].strip()
            if " to " in range_str:
                x_min_str, x_max_str = range_str.split(" to ", 1)
                try:
                    x_min, x_max = float(x_min_str), float(x_max_str)
                except ValueError:
                    x_min, x_max = -3.14, 3.14
            else:
                x_min, x_max = -3.14, 3.14
        else:
            func_str = text.strip()
            x_min, x_max = -3.14, 3.14
        
        if not func_str or len(func_str) < 2:
            return "Use: plot sin(x) from 0 to 6"
        
        # High resolution for GUI
        width = 50
        x = np.linspace(x_min, x_max, width)
        safe_globals = {"x": x, "np": np, "sin": np.sin, "cos": np.cos, "pi": np.pi, "tan": np.tan, "sqrt": np.sqrt, "exp": np.exp, "log": np.log}
        y = eval(func_str, {"__builtins__": {}}, safe_globals)
        
        # Create JSON payload
        payload = {
            "title": f"y = {func_str}",
            "x_values": x.tolist(),
            "y_values": y.tolist()
        }
        
        return "GUI_PLOT:" + json.dumps(payload)
        
    except Exception as e:
        return f"Error: {str(e)}"
