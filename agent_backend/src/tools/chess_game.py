"""
Chess Game Engine for AgentOS
Manages game state, move validation, and GUI payload generation
"""
import chess
import json
from typing import Optional, List, Dict, Any

class ChessGame:
    """Chess game state manager using python-chess"""
    
    # Unicode pieces for display
    PIECES = {
        'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔', 'P': '♙',
        'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚', 'p': '♟',
        '.': '·'
    }
    
    def __init__(self):
        self.board = chess.Board()
        self.move_history: List[str] = []
        self.game_over = False
        self.result = None
    
    def get_legal_moves(self) -> List[str]:
        """Return list of legal moves in UCI notation (e.g., 'e2e4')"""
        return [move.uci() for move in self.board.legal_moves]
    
    def make_move(self, move_uci: str) -> bool:
        """Make a move. Returns True if successful."""
        try:
            move = chess.Move.from_uci(move_uci)
            if move in self.board.legal_moves:
                self.board.push(move)
                self.move_history.append(move_uci)
                self._check_game_over()
                return True
            return False
        except:
            return False
    
    def _check_game_over(self):
        """Check if game has ended"""
        if self.board.is_checkmate():
            self.game_over = True
            self.result = "Black wins!" if self.board.turn else "White wins!"
        elif self.board.is_stalemate():
            self.game_over = True
            self.result = "Stalemate - Draw"
        elif self.board.is_insufficient_material():
            self.game_over = True
            self.result = "Draw - Insufficient material"
        elif len(self.move_history) >= 100:  # Limit for demo
            self.game_over = True
            self.result = "Draw - Move limit reached"
    
    def get_board_string(self) -> str:
        """Return ASCII representation of board"""
        lines = ["  a b c d e f g h"]
        for rank in range(7, -1, -1):
            row = f"{rank+1} "
            for file in range(8):
                piece = self.board.piece_at(chess.square(file, rank))
                if piece:
                    row += self.PIECES.get(piece.symbol(), '?') + ' '
                else:
                    row += self.PIECES['.'] + ' '
            lines.append(row)
        return '\n'.join(lines)
    
    def get_turn(self) -> str:
        """Return whose turn it is"""
        return "White" if self.board.turn else "Black"
    
    def get_fen(self) -> str:
        """Return FEN notation of current position"""
        return self.board.fen()
    
    def get_gui_payload(self) -> Dict[str, Any]:
        """Generate GUI payload for kernel rendering"""
        # Create 8x8 board array
        board_array = []
        for rank in range(7, -1, -1):
            row = []
            for file in range(8):
                piece = self.board.piece_at(chess.square(file, rank))
                row.append(piece.symbol() if piece else '.')
            board_array.append(row)
        
        return {
            "board": board_array,
            "turn": self.get_turn(),
            "move_count": len(self.move_history),
            "last_move": self.move_history[-1] if self.move_history else None,
            "game_over": self.game_over,
            "result": self.result,
            "in_check": self.board.is_check()
        }
    
    def evaluate_position(self) -> int:
        """Simple material evaluation (centipawns)"""
        piece_values = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 0}
        score = 0
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                value = piece_values.get(piece.symbol().upper(), 0)
                score += value if piece.color == chess.WHITE else -value
        return score
