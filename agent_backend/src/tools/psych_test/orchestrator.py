"""
Test Orchestrator for Agent Psychology Test
Runs both agents through all games with real-time updates
"""
import json
import time
import os
from typing import Dict, Any, List
from langchain.tools import tool

from .agents import ReActAgent, ChainOfThoughtAgent, create_agents
from .games import get_all_games, LogicGame

# PTY for streaming
_pty_fd = None
_msg_id = 0

def set_pty_fd(fd):
    global _pty_fd
    _pty_fd = fd

def send_msg(content: str):
    """Send text message to kernel shell"""
    global _pty_fd
    if _pty_fd is None:
        return
    
    # Construct a simple response message that shell.rs will print
    msg = {
        "id": int(time.time()), # distinct ID
        "target": "shell", 
        "msg_type": "response", # generic type that goes to shell
        "content": content
    }
    
    try:
        msg_str = json.dumps(msg) + "\n"
        chunk_size = 32
        for i in range(0, len(msg_str), chunk_size):
            chunk = msg_str[i:i+chunk_size]
            os.write(_pty_fd, chunk.encode('utf-8'))
            time.sleep(0.02)
    except:
        pass


def generate_leaderboard(agent_a, agent_b) -> Dict[str, Any]:
    """Generate leaderboard data"""
    a_total = sum(agent_a.scores.values())
    b_total = sum(agent_b.scores.values())
    
    # Determine winner
    if a_total > b_total:
        winner = agent_a
        loser = agent_b
        margin = ((a_total - b_total) / max(b_total, 1)) * 100
    elif b_total > a_total:
        winner = agent_b
        loser = agent_a
        margin = ((b_total - a_total) / max(a_total, 1)) * 100
    else:
        winner = None
        margin = 0
    
    # Games won
    a_wins = sum(1 for g in ["game1", "game2", "game3"] if agent_a.scores[g] > agent_b.scores[g])
    b_wins = 3 - a_wins
    
    leaderboard = {
        "rankings": [
            {
                "rank": 1,
                "agent": winner.name if winner else "TIE",
                "architecture": winner.architecture if winner else "Both",
                "total_score": max(a_total, b_total),
                "games_won": max(a_wins, b_wins),
                "is_winner": True
            },
            {
                "rank": 2,
                "agent": loser.name if winner else "TIE",
                "architecture": loser.architecture if winner else "Both",
                "total_score": min(a_total, b_total),
                "games_won": min(a_wins, b_wins),
                "is_winner": False
            }
        ] if winner else [
            {"rank": 1, "agent": "TIE", "total_score": a_total, "games_won": a_wins}
        ],
        "winner": winner.name if winner else "TIE",
        "winner_architecture": winner.architecture if winner else "Both equal",
        "margin_percent": round(margin, 1)
    }
    
    return leaderboard


def generate_analysis_report(agent_a, agent_b, game_results) -> Dict[str, Any]:
    """Generate detailed analysis report"""
    a_total = sum(agent_a.scores.values())
    b_total = sum(agent_b.scores.values())
    
    report = {
        "title": "Agent Psychology Test - Analysis Report",
        "agents": {
            "agent_a": agent_a.get_profile_dict(),
            "agent_b": agent_b.get_profile_dict()
        },
        "game_breakdown": game_results,
        "performance_comparison": {
            "agent_a": {
                "total": a_total,
                "avg_per_game": round(a_total / 3, 1),
                "best_game": max(agent_a.scores.items(), key=lambda x: x[1]),
                "worst_game": min(agent_a.scores.items(), key=lambda x: x[1])
            },
            "agent_b": {
                "total": b_total,
                "avg_per_game": round(b_total / 3, 1),
                "best_game": max(agent_b.scores.items(), key=lambda x: x[1]),
                "worst_game": min(agent_b.scores.items(), key=lambda x: x[1])
            }
        },
        "key_findings": [],
        "recommendation": ""
    }
    
    # Generate findings
    if a_total > b_total:
        diff = a_total - b_total
        report["key_findings"].append(f"Agent A (ReAct) outperformed by {diff} points")
        report["key_findings"].append("ReAct's iterative approach proved effective")
        report["recommendation"] = "Use ReAct architecture for similar reasoning tasks"
    elif b_total > a_total:
        diff = b_total - a_total
        report["key_findings"].append(f"Agent B (CoT) outperformed by {diff} points")
        report["key_findings"].append("Chain-of-Thought's structured reasoning excelled")
        report["recommendation"] = "Use CoT architecture for similar reasoning tasks"
    else:
        report["key_findings"].append("Both architectures performed equally")
        report["recommendation"] = "Either architecture suitable for this task type"
    
    # Architecture-specific insights
    report["architecture_analysis"] = {
        "react": {
            "style": "Think → Act → Observe → Repeat",
            "observed_behavior": "Iterative refinement with action steps",
            "effectiveness": f"{round(a_total/450*100)}%"
        },
        "cot": {
            "style": "Step-by-step reasoning chains",
            "observed_behavior": "Explicit logical progression",
            "effectiveness": f"{round(b_total/450*100)}%"
        }
    }
    
    return report


@tool
def run_agent_psych_test() -> str:
    """
    Run the Agent Psychology Test!
    Evaluates Pattern Recognition, Logical Deduction, and Strategic Planning.
    """
    global _msg_id
    
    # Send initial header to Kernel
    header = "\n" + "="*60 + "\n"
    header += "   🧠 AGENT PSYCHOLOGY TEST 🧠\n"
    header += "   Evaluating Agent Reasoning Capabilities\n"
    header += "="*60 + "\n"
    send_msg(header)
    
    # Create agents
    agent_a, agent_b = create_agents()
    games = get_all_games()
    game_results = []
    
    send_msg(f"\n📋 Agents Initiated:\n   Agent A: {agent_a.architecture}\n   Agent B: {agent_b.architecture}\n")
    
    # Run through each game
    for game_idx, game in enumerate(games):
        game_num = game_idx + 1
        game_key = f"game{game_num}"
        
        g_header = f"\n{'='*60}\n   GAME {game_num}: {game.name.upper()}\n{'='*60}\n"
        
        # Generate problem
        problem, correct = game.generate_problem()
        g_header += f"\n{problem[:200]}...\n"
        send_msg(g_header)
        
        game_result = {
            "game": game.name,
            "game_number": game_num,
            "problem": problem[:100],
            "agents": {}
        }
        
        # Agent A attempts
        send_msg(f">>> Agent A ({agent_a.architecture}) thinking...")
        time.sleep(0.3)
        answer_a, reasoning_a, self_score_a = agent_a.solve(problem, game.game_type)
        score_a, feedback_a = game.evaluate_answer(answer_a, correct, reasoning_a)
        agent_a.scores[game_key] = score_a
        
        res_a = f"   Answer: {answer_a[:50]}...\n   Score: {score_a}/150\n   Feedback: {feedback_a}\n"
        send_msg(res_a)
        
        game_result["agents"]["agent_a"] = {
            "answer": answer_a[:100],
            "reasoning": reasoning_a[:100],
            "score": score_a,
            "feedback": feedback_a
        }
        
        # Agent B attempts
        send_msg(f"\n>>> Agent B ({agent_b.architecture}) thinking...")
        time.sleep(0.3)
        answer_b, reasoning_b, self_score_b = agent_b.solve(problem, game.game_type)
        score_b, feedback_b = game.evaluate_answer(answer_b, correct, reasoning_b)
        agent_b.scores[game_key] = score_b
        
        res_b = f"   Answer: {answer_b[:50]}...\n   Score: {score_b}/150\n   Feedback: {feedback_b}\n"
        send_msg(res_b)
        
        game_result["agents"]["agent_b"] = {
            "answer": answer_b[:100],
            "reasoning": reasoning_b[:100],
            "score": score_b,
            "feedback": feedback_b
        }
        
        # Game winner
        if score_a > score_b:
            game_winner = "Agent A"
            send_msg(f"\n   🏆 Game {game_num} Winner: Agent A (+{score_a - score_b})\n")
        elif score_b > score_a:
            game_winner = "Agent B"
            send_msg(f"\n   🏆 Game {game_num} Winner: Agent B (+{score_b - score_a})\n")
        else:
            game_winner = "TIE"
            send_msg(f"\n   🤝 Game {game_num}: TIE\n")
        
        game_result["winner"] = game_winner
        game_results.append(game_result)
        
        time.sleep(0.5)
    
    # Generate final results
    leaderboard = generate_leaderboard(agent_a, agent_b)
    report = generate_analysis_report(agent_a, agent_b, game_results)
    
    # Format tabular summary
    summary = f"""
🧠 AGENT PSYCHOLOGY TEST COMPLETE 🧠

┌────────────────────────────────────────────────────────┐
│                    🏆 LEADERBOARD                      │
├──────┬──────────────┬──────────────────┬───────────────┤
│ Rank │ Agent        │ Architecture     │ Score         │
├──────┼──────────────┼──────────────────┼───────────────┤
"""
    for entry in leaderboard["rankings"]:
        summary += f"│ #{entry['rank']:<3} │ {entry['agent']:<12} │ {entry.get('architecture', 'Unknown')[:16]:<16} │ {entry['total_score']:>5} pts    │\n"

    summary += "└──────┴──────────────┴──────────────────┴───────────────┘\n\n"
    
    # Stage Performance
    summary += "┌────────────────────────────────────────────────────────┐\n"
    summary += "│                  🎮 STAGE PERFORMANCE                  │\n"
    summary += "├──────────┬──────────────────────┬─────────────┬────────┤\n"
    summary += "│ Stage    │ Game                 │ Winner      │ Margin │\n"
    summary += "├──────────┼──────────────────────┼─────────────┼────────┤\n"
    for res in game_results:
        g_num = res['game_number']
        g_name = res['game'][:20]
        winner = res.get('winner', 'TIE')
        s_a = res['agents']['agent_a']['score']
        s_b = res['agents']['agent_b']['score']
        margin = abs(s_a - s_b)
        summary += f"│ Game {g_num:<3} │ {g_name:<20} │ {winner:<11} │ +{margin:<5} │\n"
    summary += "└──────────┴──────────────────────┴─────────────┴────────┘\n\n"

    # SWOT Analysis
    swot = generate_swot_analysis(agent_a, agent_b, game_results)
    summary += swot + "\n"

    # Reason
    summary += "┌────────────────────────────────────────────────────────┐\n"
    summary += "│                  🧠 REASON OF CHOICE                   │\n"
    summary += "├────────────────────────────────────────────────────────┤\n"
    summary += "│ Key Findings:                                          │\n"
    for finding in report["key_findings"]:
        summary += f"│ • {finding:<52} │\n"
    summary += "├────────────────────────────────────────────────────────┤\n"
    summary += "│ Recommendation:                                        │\n"
    summary += f"│ {report['recommendation']:<54} │\n"
    summary += "└────────────────────────────────────────────────────────┘"
    
    # Send final summary to kernel as well (so it appears without needing tool return)
    # But tool return does this anyway.
    
    return summary


def generate_swot_analysis(agent_a, agent_b, game_results) -> str:
    """Generate ASCII SWOT Analysis table for both agents"""
    
    def analyze_agent(agent, opponent_scores):
        swot = {"S": [], "W": [], "O": [], "T": []}
        
        # Add static strengths
        for s in agent.strengths:
            swot["S"].append(s)
            
        # Analyze game performance
        for game_key, score in agent.scores.items():
            game_name = game_key.replace("game", "Game ")
            
            # Strengths: High score or won significantly
            if score >= 120:
                swot["S"].append(f"Excellence in {game_name} (>120)")
            elif score > opponent_scores[game_key] + 20:
                 swot["S"].append(f"Dominated {game_name}")
                 
            # Weaknesses: Low score
            if score < 100:
                swot["W"].append(f"Struggled in {game_name} (<100)")
            
            # Opportunities: Mid range or close loss
            if 100 <= score < 120:
                swot["O"].append(f"Optimize {game_name} performance")
            if score < opponent_scores[game_key] and score > opponent_scores[game_key] - 15:
                swot["O"].append(f"Close gap in {game_name}")
                
            # Threats: Very low score
            if score < 80:
                swot["T"].append(f"Failure risk in {game_name}")
                
        # Fill empty
        if not swot["W"]: swot["W"].append("None detected")
        if not swot["O"]: swot["O"].append("Maintain current performance")
        if not swot["T"]: swot["T"].append("Robust performance")
        
        return swot

    swot_a = analyze_agent(agent_a, agent_b.scores)
    swot_b = analyze_agent(agent_b, agent_a.scores)
    
    # Format table
    out =  "┌────────────────────────────────────────────────────────┐\n"
    out += "│                    📊 SWOT ANALYSIS                    │\n"
    out += "├───────────────────────────┬────────────────────────────┤\n"
    out += f"│ {agent_a.name:<25} │ {agent_b.name:<26} │\n"
    out += "├───────────────────────────┼────────────────────────────┤\n"
    
    categories = [("STRENGTHS", "S"), ("WEAKNESSES", "W"), ("OPPORTUNITIES", "O"), ("THREATS", "T")]
    
    for cat_name, cat_key in categories:
        out += f"│ {cat_name:<25} │ {cat_name:<26} │\n"
        
        items_a = swot_a[cat_key]
        items_b = swot_b[cat_key]
        max_rows = max(len(items_a), len(items_b))
        
        for i in range(max_rows):
            item_a = items_a[i] if i < len(items_a) else ""
            item_b = items_b[i] if i < len(items_b) else ""
            out += f"│ • {item_a:<23} │ • {item_b:<24} │\n"
            
        out += "├───────────────────────────┼────────────────────────────┤\n"
        
    out = out[:-60] + "└───────────────────────────┴────────────────────────────┘" # Replace last separator with footer
    return out

