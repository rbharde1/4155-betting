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
        cleaned_record = {
            "player_id": player["id"],
            "player_name": player["first_name"] + " " + player["last_name"],
            "game_id": game["id"],
            "date": game["date"],
            "pts": stat["pts"],
            "reb": stat["reb"],
            "ast": stat["ast"],
            "min": stat["min"]

        }
        cleaned_records.append(cleaned_record)

    df = pd.DataFrame(cleaned_records)

    ##Turn Minute to a int
    df["min"] = pd.to_numeric(df["min"], errors="coerce")

    ##Check minutes before removing records
    print("\nTotal raw records:", len(df))
    print("Invalid minutes:", df["min"].isna().sum())
    print("Zero-minute records:", (df["min"] == 0).sum())
    print("Players with positive minutes:", (df["min"] > 0).sum())

    ##Remove ppl who dont play
    df = df[df["min"] > 0].copy()
    
    ##Remove any accidental dupes
    df = df.drop_duplicates(
        subset=["player_id", "game_id"]
            )
    
    ##Sort by Date
    df["date"] = pd.to_datetime(df["date"])

    df = df.sort_values(
        by=["player_id", "date", "game_id"]
    ).reset_index(drop=True)



    print("\nMissing values:")
    print(df.isnull().sum())
    df = df.dropna(subset=["pts", "reb", "ast"])

    #Calcualte PR
    df["pr"] = df["pts"] + df["reb"]
    #Calculate PRA 
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

    player_stats = load_player_stats()

    print(f"Total player records loaded: {len(player_stats)}")

    df = clean_player_stats(player_stats)

    save_cleaned_data(df)

    print("\nCleaned DataFrame:")
    print(df.head())

    print(f"\nTotal rows: {len(df)}")


    print("\nCleaned DataFrame:")
    print(df.head())

    print(f"\nTotal cleaned rows: {len(df)}")
    print(f"Unique players: {df['player_id'].nunique()}")
    print(f"Unique games: {df['game_id'].nunique()}")

    print("\nSample minutes values:")
    print(df["min"].value_counts().head(15))

    print("\nInvalid minutes after conversion:")
    print(df["min"].isna().sum())


if __name__ == "__main__":
    main()