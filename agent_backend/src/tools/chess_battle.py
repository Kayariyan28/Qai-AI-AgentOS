"""
Chess Battle Orchestrator for AgentOS
Real-time AI vs AI chess with strategic analysis
"""
import json
import time
import os
from langchain.tools import tool
from .chess_game import ChessGame
from .chess_agents import get_llm_move, get_strategic_move, analyze_game

# Global reference to PTY for streaming updates
_pty_fd = None
_msg_id = 0

def set_pty_fd(fd):
    """Set the PTY file descriptor for streaming updates"""
    global _pty_fd
    _pty_fd = fd

def send_chess_update(payload: dict, msg_id: int):
    """Send a chess GUI update to the kernel"""
    global _pty_fd
    
    if _pty_fd is None:
        return
    
    msg = {
        "id": msg_id,
        "target": "kernel",
        "msg_type": "gui_chess",
        "content": json.dumps(payload)
    }
    
    try:
        msg_str = json.dumps(msg) + "\n"
        chunk_size = 32
        for i in range(0, len(msg_str), chunk_size):
            chunk = msg_str[i:i+chunk_size]
            os.write(_pty_fd, chunk.encode('utf-8'))
            time.sleep(0.02)
    except Exception as e:
        pass  # Silently fail if PTY issues


@tool
def play_chess_battle(max_moves: int = 30) -> str:
    """
    Start a REAL AI Chess Battle between two LLM Grandmaster agents!
    Watch strategic gameplay with detailed analysis.
    
    Args:
        max_moves: Maximum moves per side (default 30 = up to 60 half-moves)
    """
    global _msg_id
    game = ChessGame()
    
    move_log = []  # For analysis
    
    print("\n" + "="*60)
    print("   ♔ GRANDMASTER AI CHESS BATTLE ♚")
    print("   LLM Agent White vs LLM Agent Black")
    print("="*60)
    print("\nInitial Position:")
    print(game.get_board_string())
    print("\n>>> Game starting... Each agent will analyze and play.\n")
    
    # Send initial board
    initial_payload = game.get_gui_payload()
    initial_payload["event"] = "game_start"
    send_chess_update(initial_payload, _msg_id)
    _msg_id += 1
    
    move_num = 0
    half_moves = 0
    max_half_moves = max_moves * 2
    
    while not game.game_over and half_moves < max_half_moves:
        turn = game.get_turn()
        move_num = (half_moves // 2) + 1
        
        # Agent thinking
        print(f">>> {turn} Agent analyzing position...")
        
        # Get move with reasoning
        move, reasoning = get_llm_move(game, turn)
        
        if not move:
            print(f">>> {turn} has no legal moves!")
            break
        
        # Make the move
        score_before = game.evaluate_position()
        if game.make_move(move):
            half_moves += 1
            score_after = game.evaluate_position()
            
            from_sq = move[:2]
            to_sq = move[2:4]
            move_notation = f"{from_sq}-{to_sq}"
            
            # Log for analysis
            move_log.append({
                "move_num": move_num,
                "half_move": half_moves,
                "player": turn,
                "move": move_notation,
                "reason": reasoning,
                "score": score_after
            })
            
            # Print move with reasoning
            print(f"\n{'─'*50}")
            if half_moves % 2 == 1:
                print(f"  Move {move_num}.")
            print(f"  {turn}: {move_notation}")
            print(f"  Strategy: {reasoning}")
            if game.board.is_check():
                print(f"  ⚠️  CHECK!")
            print(f"{'─'*50}")
            print(game.get_board_string())
            
            # Real-time GUI update
            payload = game.get_gui_payload()
            payload["event"] = "move"
            payload["move_number"] = move_num
            payload["half_move"] = half_moves
            payload["move"] = move_notation
            payload["player"] = turn
            payload["reasoning"] = reasoning
            payload["score"] = score_after
            send_chess_update(payload, _msg_id)
            _msg_id += 1
            
            # Brief delay for dramatic effect
            time.sleep(0.3)
        else:
            print(f">>> Invalid move: {move}")
            break
    
    # ═══════════════════════════════════════════════════════
    # GAME ANALYSIS
    # ═══════════════════════════════════════════════════════
    
    analysis = analyze_game(game, move_log)
    
    print("\n" + "═"*60)
    print("   📊 GAME ANALYSIS")
    print("═"*60)
    
    print(f"\n🏆 RESULT: {analysis['winner']}")
    print(f"   Total Moves: {analysis['total_moves']}")
    print(f"   Margin: {analysis['winning_margin']}")
    
    if analysis['key_moves']:
        print("\n🔑 KEY MOVES:")
        for km in analysis['key_moves']:
            print(f"   • {km}")
    
    if analysis['turning_points']:
        print("\n🔄 TURNING POINTS:")
        for tp in analysis['turning_points']:
            print(f"   • Move {tp['move']}: {tp['description']}")
    
    winner_color = "White" if analysis['winner'] and "White" in analysis['winner'] else "Black"
    
    print(f"\n📋 {winner_color.upper()} AGENT'S WINNING STRATEGY:")
    strategy_list = analysis['white_strategy'] if winner_color == "White" else analysis['black_strategy']
    if strategy_list:
        for s in strategy_list:
            print(f"   ✓ {s}")
    else:
        print("   ✓ Solid positional play")
        print("   ✓ Controlled center squares")
        print("   ✓ Active piece development")
    
    print(f"\n📋 {('Black' if winner_color == 'White' else 'White').upper()} AGENT'S PLAY:")
    loser_list = analysis['black_strategy'] if winner_color == "White" else analysis['white_strategy']
    if loser_list:
        for s in loser_list[:3]:
            print(f"   • {s}")
    
    print("\n" + "═"*60)
    print("   Final Position:")
    print("═"*60)
    print(game.get_board_string())
    
    # Final GUI payload with full analysis
    final_payload = game.get_gui_payload()
    final_payload["event"] = "game_end"
    final_payload["analysis"] = analysis
    final_payload["move_history"] = [m["move"] for m in move_log]
    
    summary = f"""
GAME COMPLETE!

Winner: {analysis['winner']}
Total Moves: {analysis['total_moves']}

{winner_color} Agent demonstrated superior strategy with:
{chr(10).join(['• ' + s for s in (strategy_list or ['Solid positional play'])])}

Key tactical moments:
{chr(10).join(['• ' + km for km in (analysis['key_moves'][:3] or ['Consistent pressure throughout'])])}
"""
    
    return summary + f"\n\nGUI_CHESS:{json.dumps(final_payload)}"
