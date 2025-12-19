"""
Chess Agents for AgentOS
Advanced LLM-powered AI agents with strategic chess play
"""
import random
import chess
from typing import List, Tuple, Dict
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
import os

from .chess_game import ChessGame


def get_llm_move(game: ChessGame, color: str) -> Tuple[str, str]:
    """
    Get a move from the LLM with strategic reasoning.
    Returns (move_uci, reasoning)
    """
    try:
        model = os.getenv("AGENT_MODEL", "llama3.2")
        llm = ChatOllama(model=model, temperature=0.2)
        
        # Get board state
        board_str = game.get_board_string()
        legal_moves = game.get_legal_moves()
        eval_score = game.evaluate_position()
        
        # Categorize moves for better LLM context
        captures = []
        checks = []
        center_moves = []
        other_moves = []
        
        center_squares = ['d4', 'd5', 'e4', 'e5', 'c4', 'c5', 'f4', 'f5']
        
        for move_uci in legal_moves:
            move = game.board.parse_uci(move_uci)
            to_sq = chess.square_name(move.to_square)
            
            game.board.push(move)
            is_check = game.board.is_check()
            game.board.pop()
            
            if is_check:
                checks.append(move_uci)
            elif game.board.is_capture(move):
                captured = game.board.piece_at(move.to_square)
                piece_val = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9}.get(captured.symbol().lower(), 0) if captured else 0
                captures.append((move_uci, piece_val))
            elif to_sq in center_squares:
                center_moves.append(move_uci)
            else:
                other_moves.append(move_uci)
        
        # Sort captures by value
        captures.sort(key=lambda x: x[1], reverse=True)
        capture_moves = [c[0] for c in captures]
        
        # Strategic prompt
        system_msg = SystemMessage(content=f"""You are a GRANDMASTER chess AI playing as {color}.

STRATEGIC PRIORITIES (in order):
1. CHECKMATE if possible
2. CAPTURE high-value pieces (Queen=9, Rook=5, Bishop/Knight=3, Pawn=1)
3. GIVE CHECK to create threats
4. CONTROL the center (d4, d5, e4, e5)
5. DEVELOP pieces (Knights before Bishops, castle early)
6. PROTECT your King

RESPONSE FORMAT:
Move: [UCI format like e2e4]
Reason: [Brief tactical reason]""")
        
        move_context = f"""
Position ({game.get_turn()} to move):
{board_str}

Material: {eval_score} (positive = White ahead)
Move #{len(game.move_history) + 1}

MOVES BY TYPE:
- Checks: {', '.join(checks) or 'none'}
- Captures: {', '.join(capture_moves[:5]) or 'none'}
- Center: {', '.join(center_moves[:5]) or 'none'}
- Other: {', '.join(other_moves[:5])}...

Pick the BEST move and explain why:"""
        
        human_msg = HumanMessage(content=move_context)
        
        response = llm.invoke([system_msg, human_msg])
        response_text = response.content.strip()
        
        # Parse move and reasoning
        move = None
        reasoning = "Strategic play"
        
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.lower().startswith('move:'):
                move_text = line.split(':', 1)[1].strip().lower()
                # Extract UCI move
                for word in move_text.replace(',', ' ').replace('.', ' ').split():
                    if word in legal_moves:
                        move = word
                        break
            if line.lower().startswith('reason:'):
                reasoning = line.split(':', 1)[1].strip()[:100]  # Limit length
        
        # Fallback: try to find move anywhere in response
        if not move:
            for word in response_text.lower().replace(',', ' ').replace('.', ' ').split():
                word = word.strip()
                if word in legal_moves:
                    move = word
                    break
        
        # Ultimate fallback: use strategic heuristic
        if not move:
            move, reasoning = get_strategic_move(game, color)
        
        return move, reasoning
        
    except Exception as e:
        print(f"LLM error for {color}: {e}")
        return get_strategic_move(game, color)


def get_strategic_move(game: ChessGame, color: str) -> Tuple[str, str]:
    """Advanced heuristic move selection with reasoning"""
    
    legal_moves = list(game.board.legal_moves)
    if not legal_moves:
        return "", "No legal moves"
    
    scored_moves: List[Tuple[chess.Move, float, str]] = []
    
    for move in legal_moves:
        score = 0.0
        reason = ""
        
        # Check for checkmate
        game.board.push(move)
        if game.board.is_checkmate():
            game.board.pop()
            return move.uci(), "CHECKMATE!"
        
        # Check
        if game.board.is_check():
            score += 50
            reason = "Gives check"
        game.board.pop()
        
        # Captures (MVV-LVA: Most Valuable Victim - Least Valuable Attacker)
        if game.board.is_capture(move):
            captured = game.board.piece_at(move.to_square)
            attacker = game.board.piece_at(move.from_square)
            if captured and attacker:
                victim_val = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0}
                aggressor_val = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0}
                v = victim_val.get(captured.symbol().lower(), 0)
                a = aggressor_val.get(attacker.symbol().lower(), 1)
                score += v * 10 - a
                reason = f"Captures {captured.symbol()}"
        
        # Center control
        center = [chess.D4, chess.D5, chess.E4, chess.E5]
        if move.to_square in center:
            score += 5
            if not reason:
                reason = "Controls center"
        
        # Development bonus (early game)
        if len(game.move_history) < 10:
            piece = game.board.piece_at(move.from_square)
            if piece and piece.symbol().upper() in ['N', 'B']:
                start_rank = 0 if piece.color == chess.WHITE else 7
                if chess.square_rank(move.from_square) == start_rank:
                    score += 3
                    if not reason:
                        reason = "Develops piece"
        
        # Random tiebreaker
        score += random.random() * 0.1
        
        if not reason:
            reason = "Positional play"
        
        scored_moves.append((move, score, reason))
    
    # Pick best move
    scored_moves.sort(key=lambda x: x[1], reverse=True)
    best = scored_moves[0]
    return best[0].uci(), best[2]


def analyze_game(game: ChessGame, move_log: List[Dict]) -> Dict:
    """Generate detailed game analysis"""
    
    analysis = {
        "total_moves": len(move_log),
        "winner": None,
        "winning_margin": "equal",
        "key_moves": [],
        "white_strategy": [],
        "black_strategy": [],
        "turning_points": []
    }
    
    # Determine winner
    if game.game_over:
        if game.result and "White" in game.result:
            analysis["winner"] = "White"
        elif game.result and "Black" in game.result:
            analysis["winner"] = "Black"
        else:
            analysis["winner"] = "Draw"
    else:
        score = game.evaluate_position()
        if score > 300:
            analysis["winner"] = "White (by material)"
            analysis["winning_margin"] = "decisive"
        elif score > 100:
            analysis["winner"] = "White (slight advantage)"
            analysis["winning_margin"] = "slight"
        elif score < -300:
            analysis["winner"] = "Black (by material)"
            analysis["winning_margin"] = "decisive"
        elif score < -100:
            analysis["winner"] = "Black (slight advantage)"
            analysis["winning_margin"] = "slight"
        else:
            analysis["winner"] = "Draw (equal position)"
    
    # Extract key moves
    prev_score = 0
    for i, entry in enumerate(move_log):
        move_num = entry.get("move_num", i+1)
        player = entry.get("player", "Unknown")
        move = entry.get("move", "??")
        reason = entry.get("reason", "")
        score_after = entry.get("score", 0)
        
        # Categorize strategies
        if "check" in reason.lower() or "CHECK" in reason:
            if player == "White":
                analysis["white_strategy"].append(f"Move {move_num}: Aggressive check with {move}")
            else:
                analysis["black_strategy"].append(f"Move {move_num}: Aggressive check with {move}")
        
        if "capture" in reason.lower() or "Captures" in reason:
            if player == "White":
                analysis["white_strategy"].append(f"Move {move_num}: Material gain with {move}")
            else:
                analysis["black_strategy"].append(f"Move {move_num}: Material gain with {move}")
        
        # Detect turning points (big score swings)
        score_change = score_after - prev_score
        if abs(score_change) > 200:
            analysis["turning_points"].append({
                "move": move_num,
                "player": player,
                "description": f"{move} caused major shift ({score_change:+d})"
            })
            analysis["key_moves"].append(f"Move {move_num}: {player}'s {move} - {reason}")
        
        prev_score = score_after
    
    # Limit lists
    analysis["key_moves"] = analysis["key_moves"][:5]
    analysis["white_strategy"] = analysis["white_strategy"][:5]
    analysis["black_strategy"] = analysis["black_strategy"][:5]
    
    return analysis
