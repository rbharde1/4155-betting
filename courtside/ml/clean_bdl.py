import json
import pandas as pd
from pathlib import Path

ML_DIR = Path(__file__).resolve().parent

RAW_DATA_DIR = ML_DIR / "data" / "raw"
PROCESSED_DATA_DIR = ML_DIR / "data" / "processed"

STATS_FILE = RAW_DATA_DIR / "nba_player_stats_2024_2026.json"

def load_player_stats():
    """
    Load raw NBA player statistics from JSON.
    """

    # File paths
    ML_DIR = Path(__file__).resolve().parent

    RAW_DATA_DIR = ML_DIR / "data" / "raw"
    PROCESSED_DATA_DIR = ML_DIR / "data" / "processed"

    STATS_FILE = RAW_DATA_DIR / "nba_player_stats_2024_2026.json"


    with open(STATS_FILE,"r",encoding="utf-8") as file:
        player_stats = json.load(file)

    return player_stats

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
            "player_name": player["first_name"] + " " + player["last_name"],
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

    # Convert minutes to numeric
    df["min"] = pd.to_numeric(df["min"], errors="coerce")

    # Check minutes before removing records
    print("\nTotal raw records:", len(df))
    print("Invalid minutes:", df["min"].isna().sum())
    print("Zero-minute records:", (df["min"] == 0).sum())
    print("Players with positive minutes:", (df["min"] > 0).sum())

    # Remove players who did not play
    df = df[df["min"] > 0].copy()

    # Remove duplicate player-game records
    df = df.drop_duplicates(
        subset=["player_id", "game_id"]
    )

    # Convert date to datetime
    df["date"] = pd.to_datetime(df["date"])

    # Sort chronologically by player
    df = df.sort_values(
        by=["player_id", "date", "game_id"]
    ).reset_index(drop=True)

    # Check missing values
    print("\nMissing values:")
    print(df.isnull().sum())

    # Remove records missing essential statistics
    df = df.dropna(subset=["pts", "reb", "ast"])

    # Calculate combined player props
    df["pr"] = df["pts"] + df["reb"]
    df["pra"] = df["pts"] + df["reb"] + df["ast"]

    return df
def save_cleaned_data(df):
    """
    Save cleaned NBA player statistics to a CSV file.

    """

    ## Create directory if it doesn't exist
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    ## Define output file
    output_file = PROCESSED_DATA_DIR / "nba_player_stats_cleaned.csv"

    df.to_csv(output_file,index=False)

    print(f"\nCleaned data saved to: {output_file}")

def main():

    # Load and clean player statistics
    player_stats = load_player_stats()
    print(f"\nTotal player records loaded: {len(player_stats)}")
    df = clean_player_stats(player_stats)

    # Save cleaned dataset
    save_cleaned_data(df)

    # Display dataset summary
    print(f"\nTotal cleaned rows: {len(df)}")
    print(f"Unique players: {df['player_id'].nunique()}")
    print(f"Unique games: {df['game_id'].nunique()}")
    print("\nData cleaning completed successfully!")

if __name__ == "__main__":
    main()