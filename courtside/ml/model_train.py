import pandas as pd
from pathlib import Path

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from joblib import dump

ML_DIR = Path(__file__).resolve().parent

FEATURES_FILE = ML_DIR / "data" / "processed" / "nba_player_features.csv"

MODELS_DIR = ML_DIR / "models"

def load_features():

    df = pd.read_csv(FEATURES_FILE)

    df["date"] = pd.to_datetime(df["date"])

    return df

def prep_training_data(df,target_column):

    feature_columns = [
        # Recent performance
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
        "opp_ast_allowed_avg_10"

    ]

    #Remove players with minimal data
    df = df.dropna(subset=feature_columns + [target_column]).copy()

    X = df[feature_columns]
    y = df[target_column]

    return X, y, df

def split_training_data(X, y, df):

    ##Sort Values
    df = df.sort_values("date")

    ##Keep X/Y aligned in df
    X = X.loc[df.index]
    y = y.loc[df.index]

    ##Use 80% of games for training 
    split_index = int(len(df) * 0.8)

    ##Determine Cutoff Date
    cutoff_date = df.iloc[split_index]["date"]

    ##Split based on date
    train_mask = df["date"] < cutoff_date
    test_mask = df["date"] >= cutoff_date

    X_train = X.loc[train_mask]
    X_test = X.loc[test_mask]

    y_train = y.loc[train_mask]
    y_test = y.loc[test_mask]

    return X_train, X_test, y_train, y_test

def train_model(X_train,y_train):

    ## Initialize linear model
    model = LinearRegression()

    # Train model using historical data
    model.fit(X_train, y_train)

    return model

def evaluate_model(model, X_test, y_test):
    # Predict player points using our testing data
    predictions = model.predict(X_test)

    # Calculate Mean Absolute Error
    mae = mean_absolute_error(y_test, predictions)

    print(f"\nModel Mean Absolute Error: {mae:.2f} points")

    return predictions,mae

def evaluate_baseline(X_test, y_test, prepared_df, target):
    baseline_column = f"{target}_avg_5"
    # Predict using the previous 5-game average
    baseline_predictions = prepared_df.loc[
        X_test.index, baseline_column
    ]

    # Calculate baseline error
    baseline_mae = mean_absolute_error(
        y_test,
        baseline_predictions
    )

    return baseline_mae

def save_model(model,target,feature_columns):
    # Create models directory if it doesn't exist
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Define model file path
    model_path = MODELS_DIR / f"{target}_model.pkl"

    model_data = {  
    "model": model,
    "features": feature_columns,
    "target": target
    }

    # Save model data
    dump(model_data, model_path)

    print(f"{target.upper()} model saved to {model_path}")


def main():

    # Load engineered features
    df = load_features()

    print(f"Total records loaded: {len(df)}")

    targets = ["pts", "pr", "pra"]

    for target in targets:

        print(f"\n========== {target.upper()} MODEL ==========")

        # Prepare training data
        X, y, prepared_df = prep_training_data(df, target)

        # Split training and testing data
        X_train, X_test, y_train, y_test = split_training_data(
            X, y, prepared_df
        )

        # Train model
        model = train_model(X_train, y_train)

        # Evaluate model
        predictions, mae = evaluate_model(
            model, X_test, y_test
        )

        # Evaluate baseline
        baseline_mae = evaluate_baseline(
            X_test, y_test, prepared_df, target
    )

        # Compare model against baseline
        improvement = baseline_mae - mae

        print(f"{target.upper()} Baseline MAE: {baseline_mae:.2f}")
        print(f"{target.upper()} Improvement: {improvement:.2f}")

        final_model = train_model(X, y)

        save_model(final_model, target, X.columns.tolist())


if __name__ == "__main__":
    main()