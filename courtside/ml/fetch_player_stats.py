import os
import json
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# Load API key
load_dotenv(".env.local")

API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY was not found")

BASE_URL = "https://api.balldontlie.io/nba/v1"

HEADERS = {
    "Authorization": API_KEY
}

# File paths
ML_DIR = Path(__file__).resolve().parent

RAW_DATA_DIR = ML_DIR / "data" / "raw"

GAMES_FILE = RAW_DATA_DIR / "nba_games_2024_2026.json"

#load_games_id() Function

def load_game_ids():
    with open(GAMES_FILE, "r", encoding="utf-8") as file:
        games = json.load(file)

    game_ids = []

    for game in games:
        if game["status"] == "Final":
            game_ids.append(game["id"])

    return game_ids


def get_player_stats(game_id):
    """
    Retrieve player statistics for a single NBA game.
    """

    response = requests.get(
        f"{BASE_URL}/stats",
        headers=HEADERS,
        params={
            "game_ids[]": game_id,
            "per_page":100
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    return data["data"]


    


def main():

    game_ids = load_game_ids()

    print(f"Total game IDs loaded: {len(game_ids)}")

    # Test with the first game
    test_game_id = game_ids[0]

    print(f"\nFetching player stats for game {test_game_id}...")

    player_stats = get_player_stats(test_game_id)

    print(f"\nPlayer records collected: {len(player_stats)}")

    # Display the first five players
    for stat in player_stats[:5]:

        player = stat["player"]

        print(
            player["first_name"],
            player["last_name"],
            "| PTS:", stat["pts"],
            "| REB:", stat["reb"],
            "| AST:", stat["ast"]
        )


if __name__ == "__main__":
    main()