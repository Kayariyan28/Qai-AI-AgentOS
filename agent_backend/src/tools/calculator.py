from langchain.tools import tool
import sympy as sp

@tool
def calculator(expression: str) -> str:
    """Perform mathematical calculations, solve equations, or evaluate expressions using SymPy.
    Examples: "2 + 2", "sqrt(16)", "solve(x**2 - 4, x)", "integrate(x**2, x)"
    """
    try:
        # Use sympify to safely parse and compute
        result = sp.sympify(expression)
        if isinstance(result, sp.Expr):
            # Evaluate numerically if possible
            try:
                numerical = result.evalf()
                return f"Result: {numerical}"
            except:
                return f"Result: {result}"
        return f"Result: {result}"
    except Exception as e:
        return f"Error in calculation: {str(e)}"
