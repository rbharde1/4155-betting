import os
import json
import time
import argparse
from pathlib import Path

import requests
from dotenv import load_dotenv


# ==========================================
# 1. API CONFIGURATION
# ==========================================

ML_DIR = Path(__file__).resolve().parent
PROJECT_DIR = ML_DIR.parent

load_dotenv(PROJECT_DIR / ".env.local")

API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY was not found")

BASE_URL = "https://api.balldontlie.io/nba/v1"

HEADERS = {
    "Authorization": API_KEY
}

RAW_DATA_DIR = ML_DIR / "data" / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

HISTORICAL_GAMES_FILE = RAW_DATA_DIR / "nba_games_2024_2026.json"
HISTORICAL_STATS_FILE = RAW_DATA_DIR / "nba_player_stats_2024_2026.json"


# ==========================================
# 2. LOAD GAME IDS
# ==========================================

def load_game_ids(games_file):
    """
    Load completed NBA game IDs from a JSON file.
    """

    if not games_file.exists():
        raise FileNotFoundError(
            f"Game file not found: {games_file}"
        )

    with open(games_file, "r", encoding="utf-8") as file:
        games = json.load(file)

    game_ids = []

    for game in games:
        if game.get("status") == "Final":
            game_ids.append(game["id"])

    return list(dict.fromkeys(game_ids))


# ==========================================
# 3. API REQUEST HANDLING
# ==========================================

def make_api_request(url, params):

    max_retries = 5

    for attempt in range(max_retries):

        try:
            response = requests.get(
                url,
                headers=HEADERS,
                params=params,
                timeout=30
            )

            if response.status_code == 429:

                retry_after = response.headers.get("Retry-After")

                if retry_after and retry_after.isdigit():
                    wait_time = int(retry_after)
                else:
                    wait_time = min(60, 2 ** (attempt + 1))

                print(
                    f"Rate limit reached. "
                    f"Waiting {wait_time} seconds..."
                )

                time.sleep(wait_time)
                continue

            response.raise_for_status()

            return response.json()

        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError
        ) as error:

            wait_time = min(60, 2 ** (attempt + 1))

            print(f"Temporary API error: {error}")
            print(f"Retrying in {wait_time} seconds...")

            time.sleep(wait_time)

    raise requests.exceptions.RequestException(
        f"API request failed after {max_retries} attempts."
    )


# ==========================================
# 4. FETCH PLAYER STATISTICS
# ==========================================

def get_player_stats(game_id):
    """
    Retrieve player statistics for a single NBA game.
    """

    all_stats = []
    cursor = None

    while True:

        params = {
            "game_ids[]": game_id,
            "per_page": 100
        }

        if cursor is not None:
            params["cursor"] = cursor

        data = make_api_request(
            f"{BASE_URL}/stats",
            params
        )

        all_stats.extend(data.get("data", []))

        cursor = data.get("meta", {}).get("next_cursor")

        if cursor is None:
            break

    return all_stats


# ==========================================
# 5. SAVE PLAYER STATISTICS
# ==========================================

def save_stats(stats, output_file):
    """
    Save player statistics to JSON.
    """

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(stats, file, indent=2)

    print(f"Progress saved to: {output_file}")


# ==========================================
# 6. COLLECT PLAYER STATISTICS
# ==========================================

def collect_all_player_stats(game_ids, output_file):
    """
    Retrieve statistics for selected NBA games.

    Supports resuming previously collected data.
    """

    all_stats = []
    completed_games = set()

    # Resume previously downloaded statistics
    if output_file.exists():

        with open(output_file, "r", encoding="utf-8") as file:
            all_stats = json.load(file)

        completed_games = {
            stat["game"]["id"]
            for stat in all_stats
        }

        print(
            f"Resuming with {len(completed_games)} completed games."
        )

    new_games = 0

    for index, game_id in enumerate(game_ids, start=1):
        if game_id in completed_games:
            continue

        try:
            stats = get_player_stats(game_id)

            if not stats:
                print(
                    f"No player statistics found for game {game_id}"
                )
                continue

            all_stats.extend(stats)
            completed_games.add(game_id)
            new_games += 1

            print(
                f"Game {index}/{len(game_ids)} | "
                f"Player records: {len(all_stats)}"
            )

            # Save every 25 newly collected games
            if new_games % 25 == 0:
                save_stats(all_stats, output_file)
            time.sleep(1.5)
        except requests.exceptions.RequestException as error:

            print(
                f"Error retrieving game {game_id}: {error}"
            )

            save_stats(all_stats, output_file)
            raise

    # Final save
    save_stats(all_stats, output_file)

    print("\n========== COLLECTION SUMMARY ==========")
    print(f"Games requested: {len(game_ids)}")
    print(f"New games collected: {new_games}")
    print(f"Total player records: {len(all_stats)}")
    print("========================================")

    return all_stats


# ==========================================
# 7. MAIN PROGRAM
# ==========================================

def main():

    parser = argparse.ArgumentParser(
        description="Fetch NBA player statistics"
    )

    parser.add_argument(
        "--date",
        type=str,
        help="Fetch player statistics for YYYY-MM-DD"
    )

    args = parser.parse_args()

    if args.date:

        # Daily update mode
        games_file = RAW_DATA_DIR / f"nba_games_{args.date}.json"

        output_file = (
            RAW_DATA_DIR /
            f"nba_player_stats_{args.date}.json"
        )

        print(
            f"\nFetching player statistics for {args.date}..."
        )

    else:

        # Historical collection mode
        games_file = HISTORICAL_GAMES_FILE
        output_file = HISTORICAL_STATS_FILE

        print(
            "\nFetching historical NBA player statistics..."
        )

    # Load completed game IDs
    game_ids = load_game_ids(games_file)

    print(f"Total completed games: {len(game_ids)}")

    if not game_ids:
        print("No completed games found.")
        return

    # Fetch statistics
    collect_all_player_stats(
        game_ids,
        output_file
    )

    print("\nPlayer statistics collection completed!")


if __name__ == "__main__":
    main()