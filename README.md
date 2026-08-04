# ♟ Chess AI Move Advisor

A command-line chess coaching tool that tracks your game move by move, consults the Stockfish chess engine for the objectively best move, and uses Google's Gemini API to explain the reasoning behind it in plain language.

## Features

- **Exact board tracking**: moves are entered in standard algebraic notation (e.g. `e4`, `Nf3`, `O-O`) and validated against the real rules of chess using `python-chess`, so the board state is always accurate, no guessing involved.
- **Start from any position**: begin a fresh game, or paste an existing FEN to jump straight into a mid-game position you're already analyzing.
- **Engine-grade move recommendations**: the best move each round comes directly from Stockfish (via a free public API), not from an LLM guessing at strategy.
- **Position evaluation**: each round shows who's ahead and by roughly how much, or flags a forced checkmate sequence when one exists.
- **Plain-language explanations**: Gemini explains why Stockfish's chosen move is strong, what it defends against, and what plan it sets up.
- **Continuous game loop**: the board persists across the whole session, so you only enter each new move as it happens rather than re-describing the position every round.
- **Graceful game-over handling**: checkmate, stalemate, and draws are detected and announced clearly, with the option to start a new game without restarting the program. Illegal or inconsistent FENs (e.g. a mismatched side-to-move field) are also flagged with a clear explanation.
- **Analysis history**: every round is saved to `chess_analysis_history.json`, including the FEN, Stockfish's move, evaluation, and mate score, and the generated explanation.
- **Resilient to failures**: both the Stockfish and Gemini calls retry automatically with exponential backoff, and a top-level safety net ensures one bad round can't crash the whole session.
- **Colored terminal output**: best move, explanation, and evaluation are visually distinct for quick reading.

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/LuiCodedotjpeg/Chess-AI-Advisor.git
   cd chess-ai-advisor
   ```

2. **Create a virtual environment (optional but recommended)**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   source .venv/bin/activate   # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up your API key**
   - Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com) (no credit card required)
   - Copy `.env.example` to a new file named `.env`
   - Add your key:
     ```
     GEMINI_API_KEY=your-actual-key-here
     ```

## Usage

Run the script:
```bash
python chess_ai.py
```

You'll first be asked for a starting position: press Enter to begin a fresh game, or paste a FEN to start from an existing position. Your color and whose turn it is are determined automatically from the board.

Each round, the advisor:
1. Consults Stockfish for the objectively best move in the current position
2. Shows a position evaluation (who's ahead, or a forced mate if one exists)
3. Asks Gemini to explain why that move is strong
4. Prompts you for the move you actually played, to keep the board accurate going forward
5. Prompts for the opponent's move before the next round

You can also add optional context each round (e.g., "I'm trying to castle kingside quickly") to help shape the explanation.

When the game ends, checkmate, stalemate, or a draw, the result is announced and you're offered the option to start a new game immediately without restarting the program.

## Tech Stack

- Python
- [`python-chess`](https://python-chess.readthedocs.io/) for board state tracking, move validation, and game-over detection
- [Stockfish Online API](https://stockfish.online) for engine-grade move calculation and position evaluation
- Google Gemini API (`google-genai`) for natural-language move explanations
- `python-dotenv` for environment variable management
- `colorama` for terminal output styling
- `requests` for HTTP calls to the Stockfish API

## Notes

- Gemini model IDs change periodically as Google releases new versions. If you hit a `404` model error, check the [Gemini API changelog](https://ai.google.dev/gemini-api/docs/changelog) for the current recommended model and update the `model=` parameter in `chess_ai.py`.
- The Stockfish Online API is free and requires no API key, but as a public shared service it may occasionally be slower or rate-limited under heavy use.
- If a custom starting FEN represents an illegal position (most often a side-to-move mismatch, such as leaving the opponent in check on your turn), the tool will detect this and start a fresh game instead rather than proceeding with invalid state.
- `chess_analysis_history.json` is created locally and excluded from version control (see `.gitignore`) since it's personal usage data.