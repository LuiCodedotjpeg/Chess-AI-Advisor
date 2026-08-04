import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

import chess
import requests
from google import genai
from google.genai import types
from colorama import init, Fore, Style

init(autoreset=True)  # colorama: auto-reset color after each print

client = genai.Client()  # reads GEMINI_API_KEY or GOOGLE_API_KEY env variable

HISTORY_FILE = "chess_analysis_history.json"
MAX_RETRIES = 3
STOCKFISH_URL = "https://stockfish.online/api/s/v2.php"


def call_gemini(prompt, max_output_tokens=200):
    """Shared Gemini call with retry/backoff. Returns text or None on failure."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=max_output_tokens)
            )
            return response.text
        except Exception as e:
            print(Fore.YELLOW + f"Gemini attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                wait = 2 ** attempt  # 2s, 4s, 8s
                print(Fore.YELLOW + f"Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(Fore.RED + "All Gemini retry attempts failed. This may mean you've hit your free-tier rate limit, try again in a bit.")
                return None


def get_stockfish_move(fen, depth=12):
    """Query Stockfish Online API for the best move given a FEN. Returns (best_move, evaluation) or (None, None)."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                STOCKFISH_URL,
                params={"fen": fen, "depth": depth},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("success", True):
                print(Fore.RED + f"Stockfish API error: {data.get('data', 'unknown error')}")
                return None, None, None

            best_move_raw = data.get("bestmove", "")
            # bestmove usually comes back like "bestmove e2e4 ponder e7e5"
            best_move = best_move_raw.split()[1] if len(best_move_raw.split()) > 1 else best_move_raw
            evaluation = data.get("evaluation")
            mate = data.get("mate")
            return best_move, evaluation, mate

        except (requests.RequestException, ValueError) as e:
            print(Fore.YELLOW + f"Stockfish attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                wait = 2 ** attempt
                print(Fore.YELLOW + f"Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(Fore.RED + "All Stockfish retry attempts failed.")
                return None, None, None


def explain_move(fen, best_move_uci, board, color, context=""):
    """Use Gemini to explain why Stockfish's chosen move is strong, in the established output format."""
    try:
        san_move = board.san(chess.Move.from_uci(best_move_uci))
    except Exception:
        san_move = best_move_uci  # fall back to raw UCI if SAN conversion fails

    prompt = f"""You are a chess grandmaster coach. Stockfish, a world-class chess engine, has determined the best move for this position. Explain why this move is strong in plain language for a learning player.

Player color: {color}
Position (FEN): {fen}
Engine's chosen move: {san_move}
{"Context: " + context if context else ""}

Reply in this exact format:
BEST MOVE: {san_move}
---
EXPLANATION: [2-4 sentences: why this move is strong, what threats it handles, what plan it sets up]"""

    return call_gemini(prompt, max_output_tokens=200)


def format_evaluation(evaluation, mate=None):
    """Turn Stockfish's raw evaluation (or forced mate score) into a readable, human-facing line."""
    if mate is not None:
        try:
            mate_num = int(mate)
        except (TypeError, ValueError):
            return f"Position assessment: forced mate detected ({mate})."

        if mate_num > 0:
            return f"Position assessment: White has a forced checkmate in {mate_num} move(s)."
        elif mate_num < 0:
            return f"Position assessment: Black has a forced checkmate in {abs(mate_num)} move(s)."
        else:
            return "Position assessment: this is checkmate."

    if evaluation is None:
        return None

    try:
        score = float(evaluation)
    except (TypeError, ValueError):
        return f"Position assessment: {evaluation}"

    if score > 0:
        return f"Position assessment: White is ahead by roughly {abs(score):.2f} pawns."
    elif score < 0:
        return f"Position assessment: Black is ahead by roughly {abs(score):.2f} pawns."
    else:
        return "Position assessment: the position is roughly equal."


def print_result(result, evaluation=None, mate=None):
    if not result:
        return
    if "---" in result:
        move_part, explanation_part = result.split("---", 1)
    else:
        move_part, explanation_part = result, ""

    print(Fore.GREEN + Style.BRIGHT + move_part.strip())
    print(Fore.CYAN + explanation_part.strip())

    eval_line = format_evaluation(evaluation, mate)
    if eval_line:
        print(Fore.BLUE + eval_line)

    print()


def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(Fore.RED + f"Could not save history: {e}")


def prompt_for_legal_move(board, prompt_text):
    """Keep asking until the user enters a legal move in algebraic notation (e.g. e4, Nf3, O-O), or blank to skip."""
    while True:
        move_str = input(prompt_text).strip()
        if not move_str:
            return None
        try:
            board.push_san(move_str)
            return move_str
        except (ValueError, chess.IllegalMoveError, chess.InvalidMoveError, chess.AmbiguousMoveError):
            print(Fore.RED + f"'{move_str}' isn't a legal move in this position. Try again (e.g. e4, Nf3, O-O).")


def announce_game_over(board):
    """Print a friendly, specific message describing how the game ended."""
    if board.is_checkmate():
        # The side NOT to move just delivered the mate.
        winner = "White" if board.turn == chess.BLACK else "Black"
        print(Fore.MAGENTA + Style.BRIGHT + f"\nCheckmate! {winner} wins. Congratulations!")
    elif board.is_stalemate():
        print(Fore.MAGENTA + "\nStalemate, it's a draw.")
    elif board.is_insufficient_material():
        print(Fore.MAGENTA + "\nDraw by insufficient material.")
    else:
        print(Fore.MAGENTA + f"\nGame over: {board.result()}")


def offer_new_game():
    """Ask whether to start a fresh game or end the program. Returns a new board, or None to quit."""
    again = input(Fore.WHITE + "Start a new game from scratch? (y/n): ").strip().lower()
    if again == "y":
        return load_starting_board()
    return None


def load_starting_board():
    """Ask whether to start fresh or from an existing position, and return a validated board."""
    start_fen = input(
        "Starting position: press Enter for a fresh game, or paste a FEN to start from an existing position: "
    ).strip()

    if not start_fen:
        return chess.Board()

    try:
        return chess.Board(start_fen)
    except ValueError:
        print(Fore.RED + "That FEN isn't valid. Starting a fresh game instead.")
        return chess.Board()


def main():
    print(Fore.MAGENTA + Style.BRIGHT + "\n♟  Chess AI Move Advisor \n")
    history = load_history()
    board = load_starting_board()

    # The side to move is read directly from the board, whether it's a fresh game
    # or a custom FEN, so there's no separate "your color" question to get out of sync.
    color = "White" if board.turn == chess.WHITE else "Black"
    print(f"It's {color}'s turn to move.\n")

    move_number = 1

    while True:
        try:
            print(Fore.MAGENTA + f"\n--- Move {move_number} ({color} to move) ---")

            if board.is_game_over():
                announce_game_over(board)
                new_board = offer_new_game()
                if new_board is None:
                    break
                board = new_board
                color = "White" if board.turn == chess.WHITE else "Black"
                move_number = 1
                continue

            ctx = input("Context (optional, press Enter to skip): ").strip()
            fen = board.fen()

            print(Fore.YELLOW + "\nConsulting Stockfish...")
            best_move_uci, evaluation, mate = get_stockfish_move(fen)

            # Stockfish returning no move (or an explicit "none") means no legal move exists,
            # i.e. checkmate or stalemate, even if python-chess's own check above somehow missed it.
            if not best_move_uci or best_move_uci.strip().lower() in ("none", "(none)"):
                print(Fore.RED + "Stockfish found no legal move in this position, the game appears to be over.")
                announce_game_over(board)
                new_board = offer_new_game()
                if new_board is None:
                    break
                board = new_board
                color = "White" if board.turn == chess.WHITE else "Black"
                move_number = 1
                continue

            print(Fore.YELLOW + "Generating explanation...\n")
            result = explain_move(fen, best_move_uci, board, color, ctx)
            print_result(result, evaluation, mate)

            if result:
                history.append({
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "move_number": move_number,
                    "color": color,
                    "fen": fen,
                    "context": ctx,
                    "stockfish_move_uci": best_move_uci,
                    "stockfish_evaluation": evaluation,
                    "stockfish_mate": mate,
                    "result": result.strip()
                })
                save_history(history)

            # Record what the user actually played, so the board stays accurate going forward.
            prompt_for_legal_move(board, "Your move (what you actually played): ")

            if board.is_game_over():
                announce_game_over(board)
                new_board = offer_new_game()
                if new_board is None:
                    break
                board = new_board
                color = "White" if board.turn == chess.WHITE else "Black"
                move_number = 1
                continue

            again = input(Fore.WHITE + "Continue analyzing this game? (y/n): ").strip().lower()
            if again != "y":
                break

            # Now it's the opponent's turn; get their move before the next round of advice.
            prompt_for_legal_move(board, "Opponent's move: ")
            color = "White" if board.turn == chess.WHITE else "Black"
            move_number += 1

        except KeyboardInterrupt:
            print(Fore.MAGENTA + "\n\nSession interrupted by user.")
            break
        except Exception as e:
            # Top-level safety net: one unexpected error should never kill the whole session.
            print(Fore.RED + f"\nUnexpected error this round: {e}")
            print(Fore.RED + "Continuing to the next round rather than ending the session.\n")
            continue

    print(Fore.MAGENTA + "\nSession saved to " + HISTORY_FILE + ". Good luck out there!\n")


if __name__ == "__main__":
    main()