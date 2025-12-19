import os
import subprocess
import sys
from typing import Literal, Annotated

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, SystemMessage

# --- Configuration ---
LLM_MODEL = "llama3.2" # Or "mistral"
ALLOWED_COMMANDS = {"ls", "pwd", "mkdir", "echo", "cat", "whoami", "date", "touch"}

# --- Tools ---
from agent_backend.src.tools.music_player import play_music

@tool
def safe_shell(command: str) -> str:
    """
    Executes a shell command if it is allowed. 
    Allowed commands: ls, pwd, mkdir, echo, cat, whoami, date, touch.
    Args:
        command: The full bash command to execute (e.g., 'ls -la', 'mkdir test').
    Returns:
        The output of the command or an error message.
    """
    parts = command.split()
    if not parts:
        return "Error: Empty command."
    
    base_cmd = parts[0]
    if base_cmd not in ALLOWED_COMMANDS:
        return f"Error: Command '{base_cmd}' is not allowed. Allowed: {', '.join(sorted(ALLOWED_COMMANDS))}"

    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error executing command: {e.stderr}"

@tool
def web_search(query: str) -> str:
    """
    Performs a web search using DuckDuckGo.
    Use this for current events, factual queries, or external information.
    Args:
        query: The search query string.
    Returns:
        A summary of search results.
    """
    search = DuckDuckGoSearchRun()
    return search.run(query)

@tool
def calculator(expression: str) -> str:
    """
    Evaluates a mathematical expression symbolically or numerically using SymPy.
    Can handle arithmetic, algebra, and calculus (integrals, derivatives).
    Args:
        expression: The mathematical expression (e.g., 'integrate(x**2, x)', 'sin(pi/2)', '2 + 2').
    Returns:
        The result as a string.
    """
    import sympy
    from sympy import sympify, integrate, diff, sin, cos, tan, exp, log, pi, I, solve, Eq
    
    # whitelist allowed symbols to prevent code execution
    allowed_locals = {
        "integrate": integrate, "diff": diff,
        "sin": sin, "cos": cos, "tan": tan, 
        "exp": exp, "log": log,
        "pi": pi, "I": I,
        "solve": solve, "Eq": Eq
    }
    
    try:
        # Define symbols
        x, y, z = sympy.symbols('x y z')
        allowed_locals.update({'x': x, 'y': y, 'z': z})
        
        # Safe evaluation
        result = sympify(expression, locals=allowed_locals)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"

@tool
def plot_chart(instruction: str, data_list: list[float] = None) -> str:
    """
    Generates a plot based on instructions using Matplotlib.
    Saves the plot to 'generated_plot.png'.
    Args:
        instruction: Description of what to plot (e.g., 'plot y=x^2 from -10 to 10', 'bar chart of sales').
        data_list: Optional list of numbers for simple plots (e.g., [1, 2, 3, 4]).
    Returns:
        The path to the saved image file.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    plt.figure() # Clear previous
    filename = "generated_plot.png"
    
    try:
        instruction = instruction.lower()
        if "sin" in instruction or "cos" in instruction or "function" in instruction or "y=" in instruction:
            # Function plotting
            x = np.linspace(-np.pi, np.pi, 200)
            if "sin" in instruction:
                y = np.sin(x)
                plt.plot(x, y)
                plt.title("Plot of sin(x)")
            elif "cos" in instruction:
                y = np.cos(x)
                plt.plot(x, y)
                plt.title("Plot of cos(x)")
            elif "x^2" in instruction or "x**2" in instruction:
                x = np.linspace(-10, 10, 100)
                y = x**2
                plt.plot(x, y)
                plt.title("Plot of y=x^2")
            else:
                return "Error: Unsupported function type. Try 'sin', 'cos', or 'x^2'."
        elif "bar" in instruction and data_list:
            plt.bar(range(len(data_list)), data_list)
            plt.title("Bar Chart")
        elif "scatter" in instruction and data_list:
             plt.scatter(range(len(data_list)), data_list)
             plt.title("Scatter Plot")
        elif data_list:
            plt.plot(data_list)
            plt.title("Line Plot")
        else:
             return "Error: Please provide data_list for bar/scatter/line plots or specify a known function (sin/cos/x^2)."

        plt.savefig(filename)
        plt.close()
        return f"Plot saved to {os.path.abspath(filename)}"
    except Exception as e:
        return f"Error generating plot: {str(e)}"

# --- Agent Graph ---

tools = [safe_shell, web_search, calculator, plot_chart, play_music]

# Initialize LLM with Tools
try:
    llm = ChatOllama(model=LLM_MODEL, temperature=0)
    llm_with_tools = llm.bind_tools(tools)
except Exception as e:
    print(f"Error initializing Ollama: {e}")
    print("Is Ollama running? (ollama serve)")
    sys.exit(1)

def agent_node(state: MessagesState):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# Build Workflow
builder = StateGraph(MessagesState)
builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))

from langgraph.graph import StateGraph, MessagesState, START, END

# ...

builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")

graph = builder.compile()

# --- Public Interface ---

history_state = [SystemMessage(content="You are Qai, an advanced operating system agent. You have access to tools: Shell (safe_shell), Web Search (DuckDuckGo), Calculator (SymPy), Plotting (Matplotlib), and Music Player (play_music). Use them to help the user. If a user asks to do something unsafe (like 'rm'), politely refuse.")]

def process_command(user_input: str) -> str:
    """Processes a single command through the agent and returns the response."""
    global history_state
    
    history_state.append(HumanMessage(content=user_input))
    
    final_response = ""
    last_event = None
    
    # Stream events
    for event in graph.stream({"messages": history_state}, stream_mode="values"):
        last_event = event
    
    if last_event and "messages" in last_event:
        message = last_event["messages"][-1]
        final_response = message.content
        history_state = last_event["messages"]
    
    return final_response

# --- Main Loop ---

def main():
    print(f"🤖 Qai AgentOS Prototype (LLM: {LLM_MODEL})")
    print("Type 'quit' to exit.")
    print("---------------------------------------------")

    while True:
        try:
            user_input = input("\n👤 User: ")
            if user_input.lower() in ["quit", "exit"]:
                print("Goodbye!")
                break
            
            response = process_command(user_input)
            print(f"🤖 Qai: {response}")

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
