import pandas as pd
from pathlib import Path

ML_DIR = Path(__file__).resolve().parent
PREDICTIONS_PATH = ML_DIR / "data" / "processed" / "nba_prop_predictions.csv"

PAGE_SIZE = 15


def load_predictions():
    if not PREDICTIONS_PATH.exists():
        print("No predictions found. Run predict_props.py first.")
        return None

    df = pd.read_csv(PREDICTIONS_PATH)
    df["date"] = pd.to_datetime(df["date"])

    return df.sort_values(["date", "team_name", "player_name"])


def display_predictions(df, page):
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE

    page_df = df.iloc[start:end].copy()

    # Compact column names
    columns = {
        "player_name": "Player",
        "team_name": "Team",
        "pts_projection": "PTS",
        "pts_over_prob": "PTS O%",
        "pr_projection": "PR",
        "pr_over_prob": "PR O%",
        "pra_projection": "PRA",
        "pra_over_prob": "PRA O%"
    }

    page_df = page_df[list(columns.keys())].rename(columns=columns)

    for col in ["PTS", "PR", "PRA"]:
        page_df[col] = page_df[col].map(lambda x: f"{x:.1f}")

    for col in ["PTS O%", "PR O%", "PRA O%"]:
        page_df[col] = page_df[col].map(lambda x: f"{x * 100:.1f}%")

    print("\n" + "=" * 105)
    print(page_df.to_string(index=False))
    print("=" * 105)

    total_pages = (len(df) + PAGE_SIZE - 1) // PAGE_SIZE
    print(f"\nPage {page + 1}/{total_pages} | Total predictions: {len(df)}")


def main():
    df = load_predictions()

    if df is None or df.empty:
        return

    page = 0
    total_pages = (len(df) + PAGE_SIZE - 1) // PAGE_SIZE

    while True:
        display_predictions(df, page)

        command = input(
            "\n[N] Next | [P] Previous | [Q] Quit: "
        ).strip().lower()

        if command == "n":
            page = min(page + 1, total_pages - 1)

        elif command == "p":
            page = max(page - 1, 0)

        elif command == "q":
            print("Exiting prediction viewer.")
            break

        else:
            print("Invalid command. Use N, P, or Q.")


if __name__ == "__main__":
    main()