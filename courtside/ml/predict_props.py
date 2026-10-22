import numpy as np
import pandas as pd
import os
import requests
import time

from joblib import load
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Directory paths

ML_DIR = Path(__file__).resolve().parent
MODELS_DIR = ML_DIR / "models"
FEATURES_PATH = (
    ML_DIR / "data" / "processed" / "nba_player_features.csv"
)

def load_models():
    models = {}
    for target in ["pts", "pr", "pra"]:
        linear_path = MODELS_DIR / f"{target}_model.pkl"
        logistic_path = MODELS_DIR / f"{target}_logistic_model.pkl"
        models[target] = {
            "linear": load(linear_path),
            "logistic": load(logistic_path)
        }

    return models

def load_player_features():
    df = pd.read_csv(FEATURES_PATH)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(
        ["player_id", "date"]
    )
    print(f"Loaded {len(df)} historical player records")
    return df

def add_player_names(predictions):

    cleaned_path = (
        ML_DIR / "data" / "processed" / "nba_player_stats_cleaned.csv"
    )

    players_df = pd.read_csv(
        cleaned_path,
        usecols=["player_id", "player_name"]
    )

    players_df = players_df.drop_duplicates(
        subset=["player_id"]
    )

    # Remove existing player name columns to avoid duplicates
    predictions = predictions.drop(
        columns=[
            "player_name",
            "player_name_x",
            "player_name_y"
        ],
        errors="ignore"
    )

    # Merge player names into predictions
    predictions = predictions.merge(
        players_df,
        on="player_id",
        how="left",
        validate="many_to_one"
    )

    return predictions

def get_current_rosters(historical_df):

    load_dotenv(ML_DIR.parent / ".env.local")

    api_key = os.getenv("BALLDONTLIE_API_KEY")

    if not api_key:
        raise ValueError("BALLDONTLIE_API_KEY not found")

    url = "https://api.balldontlie.io/v1/players"

    headers = {
        "Authorization": api_key
    }

    # Only request players that exist in our dataset
    player_ids = (
        historical_df["player_id"]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    players = []

    # Fetch players in batches
    batch_size = 25

    for i in range(0, len(player_ids), batch_size):

        batch = player_ids[i:i + batch_size]

        params = {
            "player_ids[]": batch,
            "per_page": 100
        }

        for attempt in range(5):

            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )

            if response.status_code == 429:

                retry_after = response.headers.get("Retry-After")

                wait_time = (
                    float(retry_after)
                    if retry_after
                    else min(15 * (attempt + 1), 60)
                )

                print(
                    f"Rate limit reached. Waiting {wait_time} seconds..."
                )

                time.sleep(wait_time)
                continue

            response.raise_for_status()
            break

        else:
            raise RuntimeError(
                "BALLDONTLIE rate limit persisted after 5 attempts"
            )

        data = response.json()

        for player in data.get("data", []):

            team = player.get("team") or {}

            players.append({
                "player_id": player["id"],
                "player_name": (
                    f"{player['first_name']} "
                    f"{player['last_name']}"
                ),
                "current_team_id": team.get("id"),
                "team_name": team.get("full_name")
            })

        fetched = min(i + batch_size, len(player_ids))
        total = len(player_ids)

        # Display progress at approximately 50%, 75%, and 100%
        previous_fetched = i
        for milestone in [0.50, 0.75, 1.00]:
            threshold = total * milestone
            if previous_fetched < threshold <= fetched:
                print(f"Fetched {fetched}/{total} players ({int(milestone * 100)}%)")
    return pd.DataFrame(players)

def get_upcoming_games(days_ahead=7):

    load_dotenv(ML_DIR.parent / ".env.local")

    api_key = os.getenv("BALLDONTLIE_API_KEY")

    if not api_key:
        raise ValueError("BALLDONTLIE_API_KEY not found")

    today = datetime.now().date()
    end_date = today + timedelta(days=days_ahead)

    url = "https://api.balldontlie.io/v1/games"

    headers = {
        "Authorization": api_key
    }

    params = {
        "start_date": str(today),
        "end_date": str(end_date),
        "per_page": 100
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    games = response.json()["data"]

    upcoming_games = []

    for game in games:

        if game["status"] == "Final":
            continue

        upcoming_games.append({
            "game_id": game["id"],
            "date": game["date"],
            "home_team_id": game["home_team"]["id"],
            "visitor_team_id": game["visitor_team"]["id"]
        })

    return pd.DataFrame(upcoming_games)

def calculate_upcoming_opponent_defense(historical_df, upcoming_df):

    # Get each team's total statistics for completed games
    team_stats = (
        historical_df.groupby(
            ["game_id", "date", "team_id"],
            as_index=False
        )[["pts", "reb", "ast"]]
        .sum()
    )

    # Get the opponent for each team
    opponents = (
        historical_df[
            ["game_id", "team_id", "opponent_id"]
        ]
        .drop_duplicates()
    )

    # Match team statistics with the defending team
    team_stats = team_stats.merge(
        opponents,
        on=["game_id", "team_id"],
        how="left"
    )

    team_stats = team_stats.rename(
        columns={
            "opponent_id": "defending_team_id",
            "pts": "pts_allowed",
            "reb": "reb_allowed",
            "ast": "ast_allowed"
        }
    )

    # Prepare the six defensive features
    defensive_features = []

    for _, game in upcoming_df[
        ["date", "opponent_id"]
    ].drop_duplicates().iterrows():

        game_date = game["date"]
        opponent_id = game["opponent_id"]

        # Only use games completed before the upcoming matchup
        previous_games = (
            team_stats[
                (team_stats["defending_team_id"] == opponent_id)
                & (team_stats["date"] < game_date)
            ]
            .sort_values(["date", "game_id"])
        )

        features = {
            "date": game_date,
            "opponent_id": opponent_id
        }

        for stat in ["pts", "reb", "ast"]:
            for window in [5, 10]:

                features[f"opp_{stat}_allowed_avg_{window}"] = (
                    previous_games[f"{stat}_allowed"]
                    .tail(window)
                    .mean()
                )

        defensive_features.append(features)

    defensive_df = pd.DataFrame(defensive_features)

    # Remove defensive features copied from historical rows
    old_columns = [
        f"opp_{stat}_allowed_avg_{window}"
        for stat in ["pts", "reb", "ast"]
        for window in [5, 10]
    ]

    upcoming_df = upcoming_df.drop(
        columns=old_columns,
        errors="ignore"
    )

    # Attach the new defensive features
    upcoming_df = upcoming_df.merge(
        defensive_df,
        on=["date", "opponent_id"],
        how="left"
    )

    return upcoming_df


def round_to_half(value):
    """Round projections to the nearest 0.5."""
    return np.floor(np.asarray(value) * 2 + 0.5) / 2


def generate_prop_line(projection):
    """Generate a synthetic half-point betting line."""
    return np.floor(np.asarray(projection)) + 0.5

def generate_prop_predictions(models, upcoming_features):
    predictions = upcoming_features.copy()
    for target in ["pts", "pr", "pra"]:

        # Load trained models
        linear_bundle = models[target]["linear"]
        logistic_bundle = models[target]["logistic"]
        linear_model = linear_bundle["model"]
        logistic_model = logistic_bundle["model"]

        # Use exact training features
        linear_features = linear_bundle["features"]
        logistic_features = logistic_bundle["features"]

        # Generate raw player projections
        raw_projections = linear_model.predict(
            predictions[linear_features]
        )

        # Prevent negative predictions
        raw_projections = np.maximum(raw_projections, 0)

        # Round displayed projections to nearest 0.5
        rounded_projections = round_to_half(raw_projections)

        # Generate synthetic betting lines
        prop_lines = generate_prop_line(raw_projections)

        # Save projections and lines
        predictions[f"{target}_projection"] = rounded_projections
        predictions[f"{target}_line"] = prop_lines

        # Prepare logistic regression inputs
        logistic_inputs = predictions[
            [col for col in logistic_features if col != "prop_line"]
        ].copy()

        # Add generated betting lines
        logistic_inputs["prop_line"] = prop_lines
        # Restore exact training feature order
        logistic_inputs = logistic_inputs[logistic_features]

        # Calculate OVER probabilities
        over_probabilities = logistic_model.predict_proba(
            logistic_inputs
        )[:, 1]

        # Save OVER and UNDER probabilities
        predictions[f"{target}_over_prob"] = over_probabilities
        predictions[f"{target}_under_prob"] = (
            1 - over_probabilities
        )
    return predictions

def build_upcoming_player_features(historical_df,upcoming_games,current_rosters):

    historical_df = historical_df.copy()
    historical_df["date"] = pd.to_datetime(historical_df["date"])
    historical_df = historical_df.sort_values(
        ["player_id", "date", "game_id"]
    )

    upcoming_players = []

    for _, game in upcoming_games.iterrows():

        game_date = pd.to_datetime(game["date"])
        home_team_id = game["home_team_id"]
        visitor_team_id = game["visitor_team_id"]

        # Only use games played before the upcoming matchup
        previous_df = historical_df[
            historical_df["date"] < game_date
        ].copy()

        if previous_df.empty:
            continue

        # Identify each player's most recently recorded team
        latest_players = (
            previous_df.groupby("player_id")
            .tail(1)
            .copy()
        )

        # Determine the upcoming NBA season
        season = (
            game_date.year
            if game_date.month >= 7
            else game_date.year - 1
        )

        previous_df["season"] = np.where(
            previous_df["date"].dt.month >= 7,
            previous_df["date"].dt.year,
            previous_df["date"].dt.year - 1
        )

        # Calculate rolling averages
        rolling_columns = []

        for stat in ["pts", "reb", "ast", "min"]:

            for window in [5, 10]:

                column = f"{stat}_avg_{window}"

                previous_df[column] = (
                    previous_df.groupby("player_id")[stat]
                    .transform(
                        lambda x: x.rolling(
                            window=window,
                            min_periods=1
                        ).mean()
                    )
                )

                rolling_columns.append(column)

        latest_averages = (
            previous_df.groupby("player_id")
            .tail(1)[["player_id"] + rolling_columns]
        )

        # Calculate current-season averages
        season_df = previous_df[
            previous_df["season"] == season
        ]

        season_averages = (
            season_df.groupby("player_id")[
                ["pts", "reb", "ast", "min"]
            ]
            .mean()
            .rename(
                columns={
                    "pts": "pts_season_avg",
                    "reb": "reb_season_avg",
                    "ast": "ast_season_avg",
                    "min": "min_season_avg"
                }
            )
            .reset_index()
        )

        # Use previous-season averages when current-season
        # statistics are not available
        previous_season_df = previous_df[
            previous_df["season"] == season - 1
        ]

        previous_season_averages = (
            previous_season_df.groupby("player_id")[
                ["pts", "reb", "ast", "min"]
            ]
            .mean()
            .rename(
                columns={
                    "pts": "pts_season_avg",
                    "reb": "reb_season_avg",
                    "ast": "ast_season_avg",
                    "min": "min_season_avg"
                }
            )
            .reset_index()
        )

        # Prepare players for both teams
        for team_id, opponent_id, is_home in [
            (home_team_id, visitor_team_id, 1),
            (visitor_team_id, home_team_id, 0)
        ]:

            # Find players currently assigned to this team
            current_team_players = current_rosters[
                current_rosters["current_team_id"] == team_id
            ][["player_id"]]

            # Match current roster against historical player statistics
            team_players = latest_players.merge(
                current_team_players,
                on="player_id",
                how="inner"
            )

            # Use the upcoming team's ID
            team_players["team_id"] = team_id

            if team_players.empty:
                continue

            # Remove features copied from historical games
            feature_columns = (
                rolling_columns
                + [
                    "pts_season_avg",
                    "reb_season_avg",
                    "ast_season_avg",
                    "min_season_avg",
                    "rest_days",
                    "is_back_to_back"
                ]
                + [
                    f"opp_{stat}_allowed_avg_{window}"
                    for stat in ["pts", "reb", "ast"]
                    for window in [5, 10]
                ]
            )

            team_players = team_players.drop(
                columns=feature_columns,
                errors="ignore"
            )

            # Save the player's last completed game date
            team_players["last_game_date"] = team_players["date"]

            # Assign upcoming matchup information
            team_players["game_id"] = game["game_id"]
            team_players["date"] = game_date
            team_players["team_id"] = team_id
            team_players["opponent_id"] = opponent_id
            team_players["is_home"] = is_home
            team_players["season"] = season
            

            # Attach rolling averages
            team_players = team_players.merge(
                latest_averages,
                on="player_id",
                how="left"
            )

            # Attach current-season averages
            team_players = team_players.merge(
                season_averages,
                on="player_id",
                how="left"
            )

            # Attach previous-season averages as fallback
            team_players = team_players.merge(
                previous_season_averages,
                on="player_id",
                how="left",
                suffixes=("", "_previous")
            )

            # Use current-season averages when available,
            # otherwise use the player's most recent historical season

            latest_season_averages = (
                previous_df.groupby(["player_id", "season"])[
                    ["pts", "reb", "ast", "min"]
                ]
                .mean()
                .reset_index()
                .sort_values(["player_id", "season"])
                .groupby("player_id")
                .tail(1)
                .set_index("player_id")
            )

            for stat in ["pts", "reb", "ast", "min"]:

                column = f"{stat}_season_avg"
                previous_column = f"{column}_previous"
                # First try the previous season
                team_players[column] = team_players[column].fillna(
                    team_players[previous_column]
                )
                # Then try the most recent season with available data
                fallback_values = team_players["player_id"].map(
                    latest_season_averages[stat]
                )
                team_players[column] = team_players[column].fillna(
                    fallback_values
                )
                team_players = team_players.drop(
                    columns=[previous_column]
                )

                # Calculate rest days
                team_players["rest_days"] = (
                    team_players["date"]
                    - team_players["last_game_date"]
                ).dt.days - 1

            # Calculate days since the player's last game

            team_players["days_since_last_game"] = (

                team_players["date"] - team_players["last_game_date"]

            ).dt.days

            # Calculate actual rest days
            team_players["rest_days"] = (
                team_players["days_since_last_game"] - 1
            )

            # Handle offseason and extended breaks
            # Use a neutral value when the gap exceeds 14 days
            team_players["rest_days"] = np.where(
                team_players["days_since_last_game"] > 14,
                2,
                team_players["rest_days"]
            )

            # Prevent negative rest days
            team_players["rest_days"] = team_players["rest_days"].clip(lower=0)

            # Identify back-to-back games
            team_players["is_back_to_back"] = (
                team_players["days_since_last_game"] == 1
            ).astype(int)
            team_players["rest_days"] = (
                team_players["rest_days"].clip(lower=0)
                )
            team_players["is_back_to_back"] = (
                    team_players["rest_days"] == 0
                ).astype(int)
            team_players = team_players.drop(
                    columns=["last_game_date"]
                )

            # Calculate opponent defensive statistics
            team_players = calculate_upcoming_opponent_defense(
                    previous_df,
                    team_players
                )

            upcoming_players.append(team_players)

    if not upcoming_players:
        return pd.DataFrame()

    upcoming_df = pd.concat(
        upcoming_players,
        ignore_index=True
    )

    return upcoming_df

def main():

    print("\n========== NBA PLAYER PROP PREDICTOR ==========\n")

    # 1. Load models and historical data
    print("Loading prediction models...")
    models = load_models()

    print("Loading historical player features...")
    historical_df = load_player_features()

    # 2. Fetch upcoming games
    print("\nFetching upcoming NBA games...")
    upcoming_games = get_upcoming_games()

    if upcoming_games.empty:
        print("No upcoming games found.")
        return

    print(f"Found {len(upcoming_games)} upcoming games")

    # 3. Fetch current rosters
    print("\nFetching current NBA rosters...")
    current_rosters = get_current_rosters(historical_df)

    # 4. Build upcoming player features
    print("\nBuilding player features...")
    upcoming_features = build_upcoming_player_features(
        historical_df,
        upcoming_games,
        current_rosters
    )

    if upcoming_features.empty:
        print("No player features generated.")
        return

    # 5. Generate predictions
    print("\nGenerating player prop predictions...")
    predictions = generate_prop_predictions(
        models,
        upcoming_features
    )

    # 6. Attach player names and teams
    predictions = add_player_names(predictions)

    predictions = predictions.merge(
        current_rosters[
            ["player_id", "current_team_id", "team_name"]
        ].drop_duplicates(subset=["player_id"]),
        on="player_id",
        how="left"
    )

    # 7. Save predictions
    output_path = (
        ML_DIR / "data" / "processed" / "nba_prop_predictions.csv"
    )

    predictions.to_csv(output_path, index=False)

    # 8. Display summary
    print("\n========== PREDICTION SUMMARY ==========")
    print(f"Upcoming games: {len(upcoming_games)}")
    print(f"Player predictions: {len(predictions)}")
    print(f"Unique games: {predictions['game_id'].nunique()}")
    print(f"Home predictions: {(predictions['is_home'] == 1).sum()}")
    print(f"Away predictions: {(predictions['is_home'] == 0).sum()}")
    print(f"\nPredictions saved to: {output_path}")
    print("========================================\n")


if __name__ == "__main__":
    main()