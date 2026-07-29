♟ Chess AI Move Advisor
A command-line chess coaching tool that suggests the best move in a given position and explains the reasoning behind it, powered by Google's Gemini API.
Features
Move analysis - describe your position (in plain language or FEN) and get a recommended move with a short explanation of the strategy behind it
Continuous session loop - analyze multiple positions in one run without restarting the script
Analysis history - every analysis is saved to `chess\_analysis\_history.json` so you can review past sessions
Retry handling - automatically retries failed API calls with exponential backoff before giving up gracefully
Colored terminal output - best move and explanation are visually distinct for quick reading
Setup
Clone the repo
```bash
   git clone https://github.com/LuiCodebeat/chess-ai-advisor.git
   cd chess-ai-advisor
   ```
Create a virtual environment (optional but recommended)
```bash
   python -m venv .venv
   .venv\\Scripts\\activate      # Windows
   source .venv/bin/activate   # macOS/Linux
   ```
Install dependencies
```bash
   pip install -r requirements.txt
   ```
Set up your API key
Get a free Gemini API key at aistudio.google.com (no credit card required)
Copy `.env.example` to a new file named `.env`
Add your key:
```
     GEMINI\_API\_KEY=your-actual-key-here
     ```

## Usage

Run the script:

```bash
python chess\_ai.py
```
You'll be prompted for:
Your color (White/Black)
Your opponent's last move
The current board position (plain description or FEN notation)
Optional context (e.g., "we both pushed our king pawns")
The advisor returns a recommended move and a short explanation, and asks if you'd like to analyze another position before ending the session.
Tech Stack
Python
Google Gemini API (`google-genai`)
`python-dotenv` for environment variable management
`colorama` for terminal output styling
Notes
Gemini model IDs change periodically as Google releases new versions. If you hit a `404` model error, check the Gemini API changelog for the current recommended model and update the `model=` parameter in `chess\_ai.py`.
`chess\_analysis\_history.json` is created locally and excluded from version control (see `.gitignore`) since it's personal usage data.