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

def calculate_rest_days(df):
    """
    Calculate days since a player's previous game.
    Identify back-to-back games.
    """

    # Sort games chronologically
    df = df.sort_values(
        by=["player_id", "date", "game_id"]
    ).copy()

    # Find each player's previous game date
    previous_game_date = df.groupby("player_id")["date"].shift(1)

    # Calculate days between games
    df["days_since_last_game"] = (
        df["date"] - previous_game_date
    ).dt.days

    # Calculate rest days
    df["rest_days"] = (
        df["days_since_last_game"] - 1
    ).clip(lower=0)

    # Identify back-to-back games
    df["is_back_to_back"] = (
        df["days_since_last_game"] == 1
    ).astype(int)

    return df

def calculate_season_averages(df):
    """
    Calculate each player's season-to-date averages
    without including the current game.
    """
    df = df.sort_values(
        by=["player_id", "date", "game_id"]
    ).copy()

    # NBA seasons begin in the fall and continue into the next year
    df["season"] = df["date"].dt.year.where(
        df["date"].dt.month >= 7,
        df["date"].dt.year - 1
    )

    for stat in ["pts", "reb", "ast", "min"]:
        df[f"{stat}_season_avg"] = (
            df.groupby(["player_id", "season"])[stat]
            .transform(
                lambda x: x.shift(1).expanding().mean()
            )
        )

    return df

def calculate_opponent_defense(df):

    # Calculate total team statistics for each game
    team_stats = (
        df.groupby(["game_id", "date", "team_id"], as_index=False)
        [["pts", "reb", "ast"]]
        .sum()
    )

    # Find the opposing team for each team-game
    opponents = (
        df[["game_id", "team_id", "opponent_id"]]
        .drop_duplicates()
    )

    # Attach opponent IDs to team statistics
    team_stats = team_stats.merge(
        opponents,
        on=["game_id", "team_id"],
        how="left"
    )

    # Rename statistics to represent what the opponent allowed
    team_stats = team_stats.rename(
        columns={
            "opponent_id": "defending_team_id",
            "pts": "pts_allowed",
            "reb": "reb_allowed",
            "ast": "ast_allowed"
        }
    )

    # Sort each defending team's games chronologically
    team_stats = team_stats.sort_values(
        ["defending_team_id", "date", "game_id"]
    )

    # Calculate defensive averages from previous games
    for stat in ["pts", "reb", "ast"]:

        for window in [5, 10]:

            team_stats[f"opp_{stat}_allowed_avg_{window}"] = (
                team_stats.groupby("defending_team_id")[
                    f"{stat}_allowed"
                ]
                .transform(
                    lambda x: x.shift(1).rolling(
                        window=window,
                        min_periods=1
                    ).mean()
                )
            )

    # Keep only defensive features
    defensive_columns = [
        "game_id",
        "defending_team_id",
        "opp_pts_allowed_avg_5",
        "opp_pts_allowed_avg_10",
        "opp_reb_allowed_avg_5",
        "opp_reb_allowed_avg_10",
        "opp_ast_allowed_avg_5",
        "opp_ast_allowed_avg_10"
    ]

    opponent_defense = team_stats[defensive_columns]

    # Attach defensive statistics to each player's matchup
    df = df.merge(
        opponent_defense,
        left_on=["game_id", "opponent_id"],
        right_on=["game_id", "defending_team_id"],
        how="left"
    )

    # Remove unnecessary column
    df = df.drop(columns=["defending_team_id"])

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
    df = load_cleaned_stats()
    print(f"\nTotal records loaded: {len(df)}")
    df = calculate_rolling_avg(df)
    df = calculate_rest_days(df)
    df = calculate_season_averages(df)
    df = calculate_opponent_defense(df)
    save_features(df)
    print("\nFeature engineering completed successfully!")

if __name__ == "__main__":
    main()