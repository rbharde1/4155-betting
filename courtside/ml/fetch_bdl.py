import os
import json
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


# ==========================================
# 1. API CONFIGURATION
# ==========================================

# Load API key from .env.local
load_dotenv(".env.local")

API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY was not found in .env.local")

BASE_URL = "https://api.balldontlie.io/nba/v1"

HEADERS = {
    "Authorization": API_KEY
}

# NBA seasons to collect
SEASONS = [2024, 2025]

# Folder for storing raw API data
RAW_DATA_DIR = Path(__file__).resolve().parent / "data" / "raw"


# ==========================================
# 2. FETCH NBA GAMES
# ==========================================

def get_games():
    """
    Retrieve all regular-season NBA games
    from the 2024-25 and 2025-26 seasons.
    """

    games = []
    cursor = None

    while True:

        # API request parameters
        params = {
            "seasons[]": SEASONS,
            "postseason": "false",
            "per_page": 100
        }

        # Continue from the previous page
        if cursor is not None:
            params["cursor"] = cursor

        # Request game data
        response = requests.get(
            f"{BASE_URL}/games",
            headers=HEADERS,
            params=params,
            timeout=30
        )

        # Check for unsuccessful requests
        response.raise_for_status()

        # Convert response to Python dictionary
        data = response.json()

        # Add games from this page
        games.extend(data["data"])

        print(f"Games collected: {len(games)}")

        # Find the next page
        cursor = data.get("meta", {}).get("next_cursor")

        # Stop when no more pages exist
        if cursor is None:
            break

        # Small delay between requests
        time.sleep(0.5)

    return games


# ==========================================
# 3. SAVE DATA
# ==========================================

def save_json(data, filename):
    """
    Save API data to a JSON file.
    """

    # Create folder if it doesn't exist
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    file_path = RAW_DATA_DIR / filename

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)

    print(f"\nData saved to: {file_path}")


# ==========================================
# 4. MAIN PROGRAM
# ==========================================

def main():

    # Fetch NBA games
    print("\nFetching NBA games from 2024-25 and 2025-26...")
    games = get_games()

    # Display total games collected
    print(f"\nTotal games collected: {len(games)}")

    # Save raw game data
    save_json(games, "nba_games_2024_2026.json")

    print("\nNBA game collection completed successfully!")

if __name__ == "__main__":

    main()