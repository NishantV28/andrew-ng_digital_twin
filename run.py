import os
import subprocess
import sys

import dotenv

from backend.rag import STORE_PATH, build_index


def ensure_api_key() -> None:
    dotenv.load_dotenv()
    if os.environ.get("GEMINI_API_KEY"):
        return
    raise SystemExit(
        "GEMINI_API_KEY is missing. Create a .env file in the project root with GEMINI_API_KEY=your_key."
    )


def ensure_index() -> None:
    if os.path.exists(STORE_PATH):
        return
    print("Vector store not found. Building index...")
    build_index()


def main() -> None:
    ensure_api_key()
    ensure_index()
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
