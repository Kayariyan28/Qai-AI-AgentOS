"""
Logic Games for Agent Psychology Test
Dynamic Game Generation using LLM "GameMaster"
"""
import random
import os
from typing import Dict, Any, Tuple, List
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

class LogicGame:
    """Base class for logic games"""
    def __init__(self, name: str, game_type: str, difficulty: str = "medium"):
        self.name = name
        self.game_type = game_type
        self.difficulty = difficulty
        self.max_score = 150
        self.model = os.getenv("AGENT_MODEL", "llama3.2")
        self.llm = ChatOllama(model=self.model, temperature=0.8) # High temp for variety
        
    def generate_problem(self) -> Tuple[str, Any]:
        """Generate a problem. Returns (problem_text, correct_answer)"""
        raise NotImplementedError
        
    def evaluate_answer(self, given_answer: str, correct_answer: Any, reasoning: str) -> Tuple[int, str]:
        """Evaluate answer. Returns (score, feedback)"""
        raise NotImplementedError


class PatternRecognitionGame(LogicGame):
    """
    Game 1: Pattern Recognition
    Generates new number sequence patterns on the fly.
    """
    def __init__(self):
        super().__init__("Pattern Recognition", "sequence")
        
    def generate_problem(self) -> Tuple[str, Dict[str, Any]]:
        prompt = """Generate a unique pattern recognition problem involving a sequence of numbers.
        The pattern should be moderately challenging (e.g., combination of alternating, geometric, or fibonacci-like).
        
        OUTPUT FORMAT ONLY (JSON):
        {
            "sequence": [1, 2, 4, 8, 16],
            "next_number": 32,
            "pattern_description": "Powers of 2",
            "explanation": "Each number is double the previous one."
        }
        """
        
        try:
            import json
            response = self.llm.invoke(prompt).content
            # Extract JSON if needed (simple cleanup)
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
                
            data = json.loads(response.strip())
            
            problem = f"""PATTERN RECOGNITION CHALLENGE

Observe the following sequence:
{', '.join(map(str, data['sequence']))}

Question: What number comes next in this sequence?

Instructions:
1. Identify the pattern
2. Explain the pattern
3. Give the next number"""
            
            return problem, {"answer": data['next_number'], "pattern": data['pattern_description']}
            
        except Exception as e:
            # Fallback (keep one static just in case of generation failure)
            return ("Fallback Sequence: 2, 4, 6, 8. What is next?", {"answer": 10, "pattern": "Even numbers"})

    def evaluate_answer(self, given_answer: str, correct: Dict, reasoning: str) -> Tuple[int, str]:
        # Evaluation logic remains similar but could also be LLM-based for robustness
        score = 0
        feedback = []
        
        correct_val = str(correct["answer"])
        if correct_val in given_answer:
            score += 100
            feedback.append("✓ Correct answer!")
        else:
            feedback.append(f"✗ Expected {correct_val}")
            
        # Basic heuristic for reasoning
        if len(reasoning) > 20: 
            score += 50
            feedback.append("✓ Reasoning provided")
            
        return min(score, 150), " | ".join(feedback)


class LogicalDeductionGame(LogicGame):
    """
    Game 2: Logical Deduction
    Generates new syllogisms or logic puzzles.
    """
    def __init__(self):
        super().__init__("Logical Deduction", "deduction")
        
    def generate_problem(self) -> Tuple[str, Dict[str, Any]]:
        prompt = """Generate a unique logical deduction puzzle with premises and a question.
        It can be a syllogism, a spatial logic puzzle, or a truth-teller/liar puzzle.
        
        OUTPUT FORMAT ONLY (JSON):
        {
            "premises": ["Premise 1", "Premise 2"],
            "question": "The specific question asked",
            "answer": "The correct answer",
            "logical_rule": "Modus Ponens/Transitivity/etc"
        }
        """
        try:
            import json
            response = self.llm.invoke(prompt).content
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                 response = response.split("```")[1].split("```")[0]
            data = json.loads(response.strip())
            
            premises_text = "\n".join([f"  • {p}" for p in data["premises"]])
            problem = f"""LOGICAL DEDUCTION CHALLENGE

Given the following premises:
{premises_text}

Question: {data["question"]}

Instructions:
1. Analyze each premise carefully
2. Apply logical rules
3. State your conclusion with reasoning"""
            
            return problem, {"answer": data["answer"], "explanation": data["logical_rule"]}
        except:
             return ("All men are mortal. Socrates is a man. Is Socrates mortal?", {"answer": "Yes", "explanation": "Syllogism"})

    def evaluate_answer(self, given_answer: str, correct: Dict, reasoning: str) -> Tuple[int, str]:
        score = 0
        feedback = []
        
        # Use LLM to evaluate the answer semantically since it's dynamic
        eval_prompt = f"""Compare the User Answer to the Correct Answer.
        Context: {correct['explanation']}
        Correct Answer: {correct['answer']}
        User Answer: {given_answer}
        
        Is the User Answer correct? (YES/NO/PARTIAL)"""
        
        eval_res = self.llm.invoke(eval_prompt).content.upper()
        
        if "YES" in eval_res:
            score = 150
            feedback.append("✓ Correct conclusion verified by Judge")
        elif "PARTIAL" in eval_res:
            score = 75
            feedback.append("~ Partially correct")
        else:
            score = 20
            feedback.append(f"✗ Incorrect. Expected: {correct['answer']}")
            
        return score, " | ".join(feedback)


class StrategicPlanningGame(LogicGame):
    """
    Game 3: Strategic Planning
    Generates optimization or resource allocation scenarios.
    """
    def __init__(self):
        super().__init__("Strategic Planning", "optimization")
        
    def generate_problem(self) -> Tuple[str, Dict[str, Any]]:
        prompt = """Generate a short strategic planning or optimization scenario (e.g., scheduling, river crossing, knapsack problem).
        
        OUTPUT FORMAT ONLY (JSON):
        {
            "scenario": "Description of the situation and constraints",
            "question": "What is the optimal solution?",
            "optimal_solution": "The best answer",
            "key_insight": "The trick or method to solve it"
        }
        """
        try:
            import json
            response = self.llm.invoke(prompt).content
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                 response = response.split("```")[1].split("```")[0]
            data = json.loads(response.strip())
            
            problem = f"""STRATEGIC PLANNING CHALLENGE

Scenario: {data["scenario"]}

Question: {data["question"]}

Instructions:
1. Identify all constraints
2. Consider different approaches
3. Find the optimal solution
4. Explain your strategy"""
            
            return problem, {"optimal": data["optimal_solution"], "insight": data["key_insight"]}
        except:
            return ("Optimization failed. Default task.", {"optimal": "N/A", "insight": "None"})

    def evaluate_answer(self, given_answer: str, correct: Dict, reasoning: str) -> Tuple[int, str]:
         # Use LLM to evaluate complex strategy answers
        eval_prompt = f"""Evaluate the strategic quality of this answer.
        Scenario Solution: {correct['optimal']}
        Key Insight: {correct['insight']}
        
        User Answer: {given_answer}
        User Reasoning: {reasoning}
        
        Score from 0 to 150 based on correctness and strategic depth. Output ONLY the number."""
        
        try:
            score_str = self.llm.invoke(eval_prompt).content
            import re
            score = int(re.search(r'\d+', score_str).group())
            feedback = f"Judge Score: {score}/150"
        except:
            score = 70
            feedback = "Judge evaluation failed, default score."
            
        return min(score, 150), feedback


def get_all_games() -> List[LogicGame]:
    """Return all three games"""
    return [
        PatternRecognitionGame(),
        LogicalDeductionGame(),
        StrategicPlanningGame()
    ]
