import os
import requests
from dotenv import load_dotenv

load_dotenv(".env.local")

API_KEY = os.getenv("BALLDONTLIE_API_KEY")

if not API_KEY:
    raise ValueError("BALLDONTLIE_API_KEY was not found in .env.local")



url = "https://api.balldontlie.io"

headers = {
    "Authorization": API_KEY
}

game_id = 18447166

response = requests.get(
    f"{url}/nba/v1/stats",
    headers=headers,
    params={"game_ids[]": game_id},
)

response.raise_for_status()

data = response.json()



print(f"Player stats for game {game_id}:\n")

players = sorted(data["data"], key=lambda x: x["pts"], reverse=True)

for stat in players[:20]:
    player = stat["player"]
    team = stat["team"]["abbreviation"]
    print(f"{player['first_name']} {player['last_name']} ({team}): "
          f"{stat['pts']} pts, {stat['reb']} reb, {stat['ast']} ast")



