import pandas as pd
from pathlib import Path

ML_DIR = Path(__file__).resolve().parent
PROCESSED_DATA_DIR = ML_DIR / "data" / "processed"

CLEANED_STATS_FILE = PROCESSED_DATA_DIR / "nba_player_stats_cleaned.csv"
FEATURES_FILE = PROCESSED_DATA_DIR / "nba_player_features.csv"


def load_cleaned_stats():
    """
    Load cleaned NBA player statistics.
    """
    df = pd.read_csv(CLEANED_STATS_FILE)
    df["date"] = pd.to_datetime(df["date"])
    return df


def calculate_rolling_avg(df):
    """
    Calculate historical rolling averages for NBA players.
    """

    # Sort games chronologically for each player
    df = df.sort_values(
        by=["player_id", "date", "game_id"]
    ).copy()

    for stat in ["pts", "reb", "ast", "pr", "pra", "min"]:
        for window in [5, 10]:
            df[f"{stat}_avg_{window}"] = (
                df.groupby("player_id")[stat]
                .transform(
                    lambda x: x.shift(1).rolling(
                        window=window, min_periods=1
                        ).mean())
        )

    return df

def save_features(df):
    """
    Save engineered player statistics to a CSV file.
    """

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    df.to_csv(FEATURES_FILE, index=False)

    print(f"\nEngineered features saved to: {FEATURES_FILE}")
    print(f"Total saved records: {len(df)}")


def main():

    # Load cleaned player statistics
    df = load_cleaned_stats()

    print(f"\nTotal records loaded: {len(df)}")
    # Calculate rolling averages
    df = calculate_rolling_avg(df)
    # Save engineered features
    save_features(df)

    print("\nFeature engineering completed successfully!")

if __name__ == "__main__":
    main()
