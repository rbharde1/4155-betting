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

def collect_all_player_stats(game_ids):
    """
    Retrieve player statistics for all NBA games.
    Save progress and allow collection to resume.
    """

    output_file = RAW_DATA_DIR / "nba_player_stats_2024_2026.json"

    all_stats = []
    completed_games = set()

    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as file:
            all_stats = json.load(file)

        completed_games = {
            stat["game"]["id"]
            for stat in all_stats
        }

        print(f"Resuming with {len(completed_games)} completed games.")

    for index, game_id in enumerate(game_ids,start=1):

        if game_id in completed_games:
            continue

        try:
            stats = get_player_stats(game_id)

            if not stats:
                print(f"No player statistics found for game {game_id}")
                time.sleep(1.5)
                continue

            all_stats.extend(stats)
            completed_games.add(game_id)

            print(
                f"Game {index}/{len(game_ids)} | "
                f"Player records: {len(all_stats)}"
            )

            if len(completed_games) % 25 == 0:
                with open(output_file,"w",encoding="utf-8") as file:
                    json.dump(all_stats, file)

                print("Progress Saved!")

            time.sleep(1.5)

        except requests.exceptions.RequestException as error:
            print(f"Error retrieving game {game_id}: {error}")

            #Save Progress before stop
            with open(output_file, "w", encoding="utf-8") as file:
                json.dump(all_stats, file)

            print("Progress saved before stop")
            break


    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(all_stats, file)

    return all_stats





    


def main():

    # Load all game IDs from our JSON file
    game_ids = load_game_ids()

    print(f"Total game IDs loaded: {len(game_ids)}")

    print("\nStarting player statistics collection...\n")

    # Retrieve player statistics for all games
    all_stats = collect_all_player_stats(game_ids)

    # Display total records collected
    print(f"\nTotal player records collected: {len(all_stats)}")

    print("\nPlayer statistics saved to JSON!")


if __name__ == "__main__":
    main()