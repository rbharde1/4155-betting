import json
import pandas as pd
from pathlib import Path


# ==========================================
# 1. FILE CONFIGURATION
# ==========================================

ML_DIR = Path(__file__).resolve().parent

RAW_DATA_DIR = ML_DIR / "data" / "raw"
PROCESSED_DATA_DIR = ML_DIR / "data" / "processed"

# Use combined historical + new season data
STATS_FILE = RAW_DATA_DIR / "nba_player_stats_combined.json"


# ==========================================
# 2. LOAD PLAYER STATISTICS
# ==========================================

def load_player_stats():
    """
    Load combined NBA player statistics from JSON.
    """

    if not STATS_FILE.exists():
        raise FileNotFoundError(
            f"Combined dataset not found: {STATS_FILE}\n"
            "Run update_dataset.py first."
        )

    with open(STATS_FILE, "r", encoding="utf-8") as file:
        player_stats = json.load(file)

    return player_stats


def convert_minutes(value):
    if pd.isna(value):
        return float("nan")
    value = str(value).strip()

    if not value:
        return float("nan")

    try:
        if ":" in value:
            minutes, seconds = value.split(":")
            return float(minutes) + float(seconds) / 60
        return float(value)
    except ValueError:
        return float("nan")



# ==========================================
# 3. CLEAN PLAYER STATISTICS
# ==========================================

def clean_player_stats(player_stats):
    """
    Convert raw NBA player statistics into a clean DataFrame.
    """

    cleaned_records = []

    for stat in player_stats:

        player = stat["player"]
        game = stat["game"]

        team_id = stat["team"]["id"]
        home_team_id = game["home_team_id"]
        visitor_team_id = game["visitor_team_id"]

        # Determine opponent and home/away status
        is_home = int(team_id == home_team_id)

        opponent_id = (
            visitor_team_id
            if is_home
            else home_team_id
        )

        cleaned_record = {
            "player_id": player["id"],
            "player_name": (
                player["first_name"] + " " + player["last_name"]
            ),
            "game_id": game["id"],
            "date": game["date"],

            # Team information
            "team_id": team_id,
            "opponent_id": opponent_id,
            "is_home": is_home,

            # Player statistics
            "pts": stat["pts"],
            "reb": stat["reb"],
            "ast": stat["ast"],
            "min": stat["min"]
        }

        cleaned_records.append(cleaned_record)

    df = pd.DataFrame(cleaned_records)

    # Convert minutes into numeric values
    df["min"] = df["min"].apply(convert_minutes)

    # Check minutes before removing records
    print("\n========== RAW DATA SUMMARY ==========")
    print(f"Total raw records: {len(df)}")
    print(f"Invalid minutes: {df['min'].isna().sum()}")
    print(f"Zero-minute records: {(df['min'] == 0).sum()}")
    print(f"Players with positive minutes: {(df['min'] > 0).sum()}")

    # Remove players who did not play
    df = df[df["min"] > 0].copy()

    # Remove duplicate player-game records
    df = df.drop_duplicates(
        subset=["player_id", "game_id"],
        keep="last"
    )

    # Convert date to datetime
    df["date"] = pd.to_datetime(df["date"])

    # Remove records missing essential statistics
    df = df.dropna(
        subset=["pts", "reb", "ast"]
    )

    # Sort chronologically by player
    df = df.sort_values(
        by=["player_id", "date", "game_id"]
    ).reset_index(drop=True)

    # Calculate combined player props
    df["pr"] = df["pts"] + df["reb"]
    df["pra"] = df["pts"] + df["reb"] + df["ast"]

    print("\n========== CLEANED DATA SUMMARY ==========")
    print(f"Cleaned player records: {len(df)}")
    print(f"Unique players: {df['player_id'].nunique()}")
    print(f"Unique games: {df['game_id'].nunique()}")
    print(f"Earliest game: {df['date'].min().date()}")
    print(f"Latest game: {df['date'].max().date()}")

    print("\nMissing values:")
    print(df.isnull().sum())

    return df


# ==========================================
# 4. SAVE CLEANED DATA
# ==========================================

def save_cleaned_data(df):
    """
    Save cleaned NBA player statistics to CSV.
    """

    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        PROCESSED_DATA_DIR / "nba_player_stats_cleaned.csv"
    )

    df.to_csv(output_file, index=False)

    print(f"\nCleaned data saved to: {output_file}")


# ==========================================
# 5. MAIN PROGRAM
# ==========================================

def main():

    print("\n========== NBA DATA CLEANING ==========\n")

    # Load combined player statistics
    player_stats = load_player_stats()

    print(f"Total player records loaded: {len(player_stats)}")

    # Clean statistics
    df = clean_player_stats(player_stats)

    # Save cleaned dataset
    save_cleaned_data(df)

    print("\nData cleaning completed successfully!")


if __name__ == "__main__":
    main()