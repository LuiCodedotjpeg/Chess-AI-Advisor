import json
import os
import time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

from google import genai
from google.genai import types
from colorama import init, Fore, Style

init(autoreset=True)  # colorama: auto-reset color after each print

client = genai.Client()  # reads GEMINI_API_KEY or GOOGLE_API_KEY env variable

HISTORY_FILE = "chess_analysis_history.json"
MAX_RETRIES = 3


def get_best_move(color, opp_move, position, context=""):
    prompt = f"""You are a chess grandmaster coach. Give the single best move for this position.

Player color: {color}
Opponent's last move: {opp_move}
Board position: {position}
{"Context: " + context if context else ""}

Reply in this exact format:
BEST MOVE: [move in algebraic notation]
---
EXPLANATION: [2-4 sentences: why this move, what threats it handles, what plan it sets up]"""

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=200)
            )
            return response.text
        except Exception as e:
            print(Fore.YELLOW + f"Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                wait = 2 ** attempt  # 2s, 4s, 8s
                print(Fore.YELLOW + f"Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(Fore.RED + "All retry attempts failed. Skipping this analysis.")
                return None

def print_result(result):
    if not result:
        return
    if "---" in result:
        move_part, explanation_part = result.split("---", 1)
    else:
        move_part, explanation_part = result, ""

    print(Fore.GREEN + Style.BRIGHT + move_part.strip())
    print(Fore.CYAN + explanation_part.strip())
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


def main():
    print(Fore.MAGENTA + Style.BRIGHT + "\n♟  Chess AI Advisor\n")
    history = load_history()

    while True:
        color = input(Fore.WHITE + "Your color (White/Black): ").strip() or "White"
        opp = input("Opponent's last move: ").strip()
        pos = input("Board position (describe or FEN): ").strip()
        ctx = input("Context (optional, press Enter to skip): ").strip()

        print(Fore.YELLOW + "\nAnalyzing...\n")
        result = get_best_move(color, opp, pos, ctx)
        print_result(result)

        if result:
            history.append({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "color": color,
                "opponent_move": opp,
                "position": pos,
                "context": ctx,
                "result": result.strip()
            })
            save_history(history)

        again = input(Fore.WHITE + "Analyze another move? (y/n): ").strip().lower()
        if again != "y":
            break

    print(Fore.MAGENTA + "\nSession saved to " + HISTORY_FILE + ". Good luck out there!\n")


if __name__ == "__main__":
    main()