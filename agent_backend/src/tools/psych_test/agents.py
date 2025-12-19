"""
Agent Architectures for Psychology Test
REAL Implementation using LangGraph and LangChain
"""
import os
import operator
from typing import Dict, Any, Tuple, List, Union, Annotated, Sequence
from langchain_ollama import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage, FunctionMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from typing import TypedDict

# ==========================================
# Shared Setup
# ==========================================

class AgentProfile:
    """Base agent profile"""
    def __init__(self, name: str, architecture: str, description: str, strengths: list, model: str = None):
        self.name = name
        self.architecture = architecture
        self.description = description
        self.strengths = strengths
        self.model = model or os.getenv("AGENT_MODEL", "llama3.2")
        self.scores = {"game1": 0, "game2": 0, "game3": 0}
        self.responses = []
        
    def get_profile_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "architecture": self.architecture,
            "description": self.description,
            "strengths": self.strengths,
            "model": self.model,
            "total_score": sum(self.scores.values())
        }

# ==========================================
# AGENT A: ReAct (LangGraph Implementation)
# ==========================================

class ReActState(TypedDict):
    """Items in the ReAct state"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    thought: str
    action: str
    key_value: str
    final_answer: str

class ReActAgent(AgentProfile):
    """
    Agent A: ReAct (Reasoning + Acting)
    Implementation: LangGraph cyclic graph (Think -> Act -> Ponder -> Loop/End)
    """
    def __init__(self):
        super().__init__(
            name="Agent A",
            architecture="ReAct (LangGraph)",
            description="Cyclic graph of Thought-Action-Observation",
            strengths=["Tool emulation", "structured loops", "iterative solving"]
        )
        self.llm = ChatOllama(model=self.model, temperature=0.3)
        self.app = self._build_graph()
        
    def _build_graph(self):
        # Nodes
        def reason_node(state):
            messages = state['messages']
            prompt = """Analyze the situation.
            You have access to a simulated calculator tool if needed (just ask).
            
            Output your THOUGHT process.
            If you have enough info, output FINAL ANSWER: [answer].
            If you need to act, output ACTION: [action description].
            """
            response = self.llm.invoke([SystemMessage(content=prompt)] + messages)
            return {"messages": [response], "thought": response.content}

        def action_node(state):
            last_msg = state['messages'][-1].content
            action = "Simulating action..."
            
            # Simple heuristic action simulation for the "Psych Test" context
            if "calculate" in last_msg.lower():
                import re
                nums = re.findall(r'\d+', last_msg)
                if len(nums) >= 2:
                    action = f"Calculated: {int(nums[0]) + int(nums[1])} (Simulated)"
            
            return {"messages": [AIMessage(content=f"OBSERVATION: {action}")], "action": action}

        # Build Graph
        workflow = StateGraph(ReActState)
        workflow.add_node("reason", reason_node)
        workflow.add_node("act", action_node)
        
        workflow.set_entry_point("reason")
        
        def should_continue(state):
            content = state['messages'][-1].content
            if "FINAL ANSWER:" in content:
                return "end"
            return "continue"
            
        workflow.add_conditional_edges(
            "reason",
            should_continue,
            {
                "continue": "act",
                "end": END
            }
        )
        workflow.add_edge("act", "reason")
        
        return workflow.compile()

    def solve(self, problem: str, problem_type: str) -> Tuple[str, str, int]:
        inputs = {"messages": [HumanMessage(content=f"Problem: {problem}")]}
        
        final_answer = ""
        reasoning_log = ""
        
        try:
            # Run graph (limit steps to prevent infinite loops)
            for output in self.app.stream(inputs, {"recursion_limit": 10}):
                for key, value in output.items():
                    if "thought" in value:
                        reasoning_log += f"\n[Thought]: {value['thought'][:100]}..."
                        if "FINAL ANSWER:" in value['thought']:
                            final_answer = value['thought'].split("FINAL ANSWER:")[1].strip()
            
            if not final_answer:
                final_answer = "Analysis incomplete."
                
            self.responses.append({"problem": problem[:30], "answer": final_answer, "reasoning": reasoning_log})
            return final_answer, reasoning_log, 120 # Base score for using the graph correctly
            
        except Exception as e:
            return "Error", str(e), 0


# ==========================================
# AGENT B: Chain-of-Thought (LangGraph)
# ==========================================

class CoTState(TypedDict):
    """Items in CoT state"""
    problem: str
    step1: str
    step2: str
    step3: str
    conclusion: str

class ChainOfThoughtAgent(AgentProfile):
    """
    Agent B: Chain of Thought
    Implementation: Sequential Graph (Step1 -> Step2 -> Step3 -> Conclusion)
    """
    def __init__(self):
        super().__init__(
            name="Agent B",
            architecture="Chain-of-Thought (LangGraph)",
            description="Sequential processing graph",
            strengths=["Depth", "Linear Logic", "Completeness"]
        )
        self.llm = ChatOllama(model=self.model, temperature=0.1)
        self.app = self._build_graph()
        
    def _build_graph(self):
        def step1_node(state):
            p = state['problem']
            res = self.llm.invoke(f"Problem: {p}\n\nStep 1: Analyze the key terms and constraints.").content
            return {"step1": res}
            
        def step2_node(state):
            prev = state['step1']
            res = self.llm.invoke(f"Based on: {prev}\n\nStep 2: Apply logical rules or mathematical operations.").content
            return {"step2": res}
            
        def step3_node(state):
            prev = state['step2']
            res = self.llm.invoke(f"Based on: {prev}\n\nStep 3: Verify and refine.").content
            return {"step3": res}
            
        def conclusion_node(state):
            steps = f"1. {state['step1']}\n2. {state['step2']}\n3. {state['step3']}"
            res = self.llm.invoke(f"Based on these steps:\n{steps}\n\nGive the FINAL ANSWER.").content
            return {"conclusion": res}
            
        workflow = StateGraph(CoTState)
        workflow.add_node("step1", step1_node)
        workflow.add_node("step2", step2_node)
        workflow.add_node("step3", step3_node)
        workflow.add_node("finalize", conclusion_node)
        
        workflow.set_entry_point("step1")
        workflow.add_edge("step1", "step2")
        workflow.add_edge("step2", "step3")
        workflow.add_edge("step3", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()

    def solve(self, problem: str, problem_type: str) -> Tuple[str, str, int]:
        inputs = {"problem": problem}
        
        try:
            result = self.app.invoke(inputs)
            
            final_ans = result.get("conclusion", "No conclusion")
            reasoning = f"Step 1: {result.get('step1')[:50]}...\nStep 2: {result.get('step2')[:50]}..."
            
            self.responses.append({"problem": problem[:30], "answer": final_ans, "reasoning": reasoning})
            return final_ans, reasoning, 130 # Bonus for structured depth
            
        except Exception as e:
            return "Error", str(e), 0

def create_agents() -> Tuple[ReActAgent, ChainOfThoughtAgent]:
    """Create both agent instances"""
    return ReActAgent(), ChainOfThoughtAgent()
