import pandas as pd
import numpy as np

from pathlib import Path
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

from joblib import dump


ML_DIR = Path(__file__).resolve().parent

FEATURES_FILE = ML_DIR / "data" / "processed" / "nba_player_features.csv"

MODELS_DIR = ML_DIR / "models"

def load_features():
    df = pd.read_csv(FEATURES_FILE)

    df["date"] = pd.to_datetime(df["date"])

    return df

def prepare_logistic_data(df, target):

    # Features used by our linear regression models
    feature_columns = [
        "pts_avg_5",
        "pts_avg_10",
        "reb_avg_5",
        "reb_avg_10",
        "ast_avg_5",
        "ast_avg_10",
        "min_avg_5",
        "min_avg_10",
        "is_home",
        "rest_days",
        "is_back_to_back",
        "pts_season_avg",
        "reb_season_avg",
        "ast_season_avg",
        "min_season_avg"
    ]

    # Remove records missing necessary information
    df = df.dropna(
        subset=feature_columns + [target]
    ).copy()

    # Sort chronologically
    df = df.sort_values(
        ["date", "game_id", "player_id"]
    ).reset_index(drop=True)

    # Store historical predictions
    df["linear_prediction"] = np.nan

    # Create chronological training splits
    unique_dates = np.array(sorted(df["date"].unique()))
    tscv = TimeSeriesSplit(n_splits=5)

    for train_dates, test_dates in tscv.split(unique_dates):
        training_dates = unique_dates[train_dates]
        testing_dates = unique_dates[test_dates]
        train_mask = df["date"].isin(training_dates)
        test_mask = df["date"].isin(testing_dates)

        # Train linear regression on earlier games
        model = LinearRegression()

        model.fit(
            df.loc[train_mask, feature_columns],
            df.loc[train_mask, target]
        )
        # Predict later games
        predictions = model.predict(
            df.loc[test_mask, feature_columns]
        )
        df.loc[test_mask, "linear_prediction"] = predictions

    # Remove games without historical predictions
    df = df.dropna(
        subset=["linear_prediction"]
    ).copy()

    # Generate our own half-point prop lines
    df["prop_line"] = (
        np.floor(df["linear_prediction"]) + 0.5
    )

    # Determine actual over/under outcomes
    df["over"] = (
        df[target] > df["prop_line"]
    ).astype(int)

    return df

def prep_training_data(df):

    feature_columns = [
        # Recent player performance
        "pts_avg_5",
        "pts_avg_10",
        "reb_avg_5",
        "reb_avg_10",
        "ast_avg_5",
        "ast_avg_10",
        "min_avg_5",
        "min_avg_10",

        # Game context
        "is_home",
        "rest_days",
        "is_back_to_back",

        # Season-to-date performance
        "pts_season_avg",
        "reb_season_avg",
        "ast_season_avg",
        "min_season_avg",

        # Opponent defensive statistics
        "opp_pts_allowed_avg_5",
        "opp_pts_allowed_avg_10",
        "opp_reb_allowed_avg_5",
        "opp_reb_allowed_avg_10",
        "opp_ast_allowed_avg_5",
        "opp_ast_allowed_avg_10",
        
        # Betting line
        "prop_line"
    ]

    # Remove rows with missing features
    df = df.dropna(
        subset=feature_columns + ["over"]
    ).copy()
    X = df[feature_columns]
    # 1 = Over, 0 = Under
    y = df["over"]

    return X, y, df

def split_training_data(X, y, df):
    """
    Split training and testing data chronologically.
    """

    # Sort records by date
    df = df.sort_values("date")

    # Keep features and labels aligned
    X = X.loc[df.index]
    y = y.loc[df.index]

    # Use approximately 80% for training
    split_index = int(len(df) * 0.8)
    cutoff_date = df.iloc[split_index]["date"]

    # Separate historical and future games
    train_mask = df["date"] < cutoff_date
    test_mask = df["date"] >= cutoff_date
    X_train = X.loc[train_mask]
    X_test = X.loc[test_mask]
    y_train = y.loc[train_mask]
    y_test = y.loc[test_mask]

    return X_train, X_test, y_train, y_test

def train_model(X_train, y_train):

    """
    Train a logistic regression model to predict
    the probability of going over a player prop line.
    """

    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1000)
    )

    model.fit(X_train, y_train)

    return model

def evaluate_model(model, X_test, y_test):
    """""
    Evaluate logistic regression predictions.
    """

    # Probability of going over the prop line
    probabilities = model.predict_proba(X_test)[:, 1]

    # Convert probabilities into binary predictions
    predictions = (probabilities >= 0.5).astype(int)

    # Evaluate performance
    accuracy = accuracy_score(y_test, predictions)
    loss = log_loss(y_test, probabilities)
    brier = brier_score_loss(y_test, probabilities)

    print(f"\nModel Accuracy: {accuracy:.2%}")
    print(f"Model Log Loss: {loss:.4f}")
    print(f"Model Brier Score: {brier:.4f}")
    return probabilities, accuracy, loss, brier

def evaluate_baseline(y_train, y_test):

    # Historical percentage of games that went over
    baseline_probability = y_train.mean()

    # Predict the same probability for every test game
    baseline_probabilities = np.full(
        len(y_test),
        baseline_probability
    )

    # Convert probabilities to over/under predictions
    baseline_predictions = (
        baseline_probabilities >= 0.5
    ).astype(int)

    accuracy = accuracy_score(
        y_test,
        baseline_predictions
    )

    loss = log_loss(
        y_test,
        baseline_probabilities,
        labels=[0, 1]
    )

    brier = brier_score_loss(
        y_test,
        baseline_probabilities
    )

    print("\n========== BASELINE ==========")
    print(f"Baseline Over Probability: {baseline_probability:.2%}")
    print(f"Baseline Accuracy: {accuracy:.2%}")
    print(f"Baseline Log Loss: {loss:.4f}")
    print(f"Baseline Brier Score: {brier:.4f}")

def save_model(model, feature_columns, target):

    # Create models directory if it doesn't exist
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Create file path for the model
    model_path = MODELS_DIR / f"{target}_logistic_model.pkl"

    # Store model and its information
    model_bundle = {
        "model": model,
        "features": feature_columns,
        "target": target
    }

    # Save model
    dump(model_bundle, model_path)

    print(f"\n{target.upper()} logistic model saved to {model_path}")

def main():

    df = load_features()

    print(f"Total records loaded: {len(df)}")

    for target in ["pts", "pr", "pra"]:

        print(f"\n========== {target.upper()} MODEL ==========")

        # Generate historical lines using linear regression
        target_df = prepare_logistic_data(df, target)

        # Prepare features and labels
        X, y, target_df = prep_training_data(target_df)

        print(f"\nTraining features shape: {X.shape}")
        print(f"Training labels shape: {y.shape}")

        # Chronological split
        X_train, X_test, y_train, y_test = split_training_data(
            X, y, target_df
        )

        print(f"\nTraining records: {len(X_train)}")
        print(f"Testing records: {len(X_test)}")

        # Train logistic regression
        model = train_model(X_train, y_train)

        # Evaluate model
        evaluate_model(model, X_test, y_test)

        # Compare against baseline
        evaluate_baseline(y_train, y_test)

        save_model(
            model,
            X.columns.tolist(),
            target
        )

if __name__ == "__main__":
    main()