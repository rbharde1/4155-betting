import json
from pathlib import Path

import pandas as pd


# ==========================================
# 1. FILE CONFIGURATION
# ==========================================

ML_DIR = Path(__file__).resolve().parent

RAW_DATA_DIR = ML_DIR / "data" / "raw"

HISTORICAL_FILE = (
    RAW_DATA_DIR / "nba_player_stats_2024_2026.json"
)

OUTPUT_FILE = (
    RAW_DATA_DIR / "nba_player_stats_combined.json"
)


# ==========================================
# 2. LOAD PLAYER STATISTICS
# ==========================================

def load_json_file(file_path):
    """
    Load player statistics from a JSON file.
    """

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


# ==========================================
# 3. FIND ALL DATASET FILES
# ==========================================

def get_dataset_files():
    """
    Find historical and daily player statistics files.
    """

    files = []

    # Original historical dataset
    if HISTORICAL_FILE.exists():
        files.append(HISTORICAL_FILE)

    # New daily datasets
    daily_files = sorted(
        RAW_DATA_DIR.glob("nba_player_stats_????-??-??.json")
    )

    files.extend(daily_files)

    return files


# ==========================================
# 4. COMBINE DATASETS
# ==========================================

def combine_datasets():

    dataset_files = get_dataset_files()

    if not dataset_files:
        print("No player statistics files found.")
        return []

    all_stats = []

    print("\n========== COMBINING NBA DATASETS ==========\n")

    for file_path in dataset_files:

        stats = load_json_file(file_path)

        print(
            f"Loaded {len(stats)} records from "
            f"{file_path.name}"
        )

        all_stats.extend(stats)

    print(f"\nTotal records before cleaning: {len(all_stats)}")

    # Remove duplicate player-game records
    unique_stats = {}

    for stat in all_stats:

        game_id = stat.get("game", {}).get("id")
        player_id = stat.get("player", {}).get("id")

        if game_id is None or player_id is None:
            continue

        key = (game_id, player_id)

        unique_stats[key] = stat

    combined_stats = list(unique_stats.values())

    # Sort records by game date
    combined_stats.sort(
        key=lambda stat: (
            stat.get("game", {}).get("date", ""),
            stat.get("game", {}).get("id", 0),
            stat.get("player", {}).get("id", 0)
        )
    )

    print(f"Records after removing duplicates: {len(combined_stats)}")

    print(
        f"Duplicate records removed: "
        f"{len(all_stats) - len(combined_stats)}"
    )

    return combined_stats


# ==========================================
# 5. SAVE COMBINED DATASET
# ==========================================

def save_combined_dataset(stats):

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(stats, file, indent=2)

    print(f"\nCombined dataset saved to: {OUTPUT_FILE}")


# ==========================================
# 6. MAIN PROGRAM
# ==========================================

def main():

    combined_stats = combine_datasets()

    if not combined_stats:
        print("No player statistics to combine.")
        return

    save_combined_dataset(combined_stats)

    print("\n========== DATASET SUMMARY ==========")
    print(f"Total player-game records: {len(combined_stats)}")

    dates = [
        stat["game"]["date"]
        for stat in combined_stats
        if stat.get("game", {}).get("date")
    ]

    if dates:
        print(f"Earliest game: {min(dates)}")
        print(f"Latest game: {max(dates)}")

    print("=====================================\n")


if __name__ == "__main__":
    main()