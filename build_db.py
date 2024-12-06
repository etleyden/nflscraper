import sys, json, requests, warnings, os
import psycopg2
from datetime import datetime
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
import pandas as pd


if len(sys.argv) > 1:
    year = int(sys.argv[1])
else:
    print("Usage: python build_db.py [YEAR]")
    sys.exit()

def safe_float_conversion(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0
    
class nflscraper():
    __loc = Nominatim(user_agent="GetLoc")
    __division = {
        12: ["AFC", "N"],
        13: ["AFC", "S"],
        4: ["AFC", "E"],
        6: ["AFC", "W"],
        10: ["NFC", "N"],
        11: ["NFC", "S"],
        1: ["NFC", "E"],
        3: ["NFC", "W"],
    }
    # Load environment variables from .env file
    load_dotenv()
    warnings.filterwarnings("ignore", category=FutureWarning)
    def __init__(self):
        return
    def get_weather_by_coordinates(self, lat, lon, date, time):
        """
        Fetches weather data for a specific location, date, and time using the Visual Crossing API.
        
        Parameters:
        - lat (float): Latitude of the location.
        - lon (float): Longitude of the location.
        - date (str): Date in 'YYYY-MM-DD' format.
        - time (str): Time in 'HH:MM' (24-hour format).
        
        Returns:
        - dict: Weather data for the specified date, time, and location.
        """
        
        # Get API key from environment variables
        api_key = os.getenv("VISUAL_CROSSING_API_KEY")
        if not api_key:
            raise ValueError("API key is missing. Please add it to the .env file.")
        
        # Combine date and time, then convert to a datetime object
        datetime_obj = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        
        # Visual Crossing API endpoint for weather data
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{lat},{lon}/{date}?unitGroup=metric&key={api_key}&contentType=json"
        
        # Make the request to the Visual Crossing API
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            for hourly in data['days'][0]['hours']:
                hourly_time = datetime.strptime(f"{data['days'][0]['datetime']}T{hourly['datetime']}Z", "%Y-%m-%dT%H:%M:%SZ")
                if hourly_time == datetime_obj:
                    return {
                        "time": hourly_time.strftime('%Y-%m-%d %H:%M:%S'),
                        "temperature": hourly['temp'],
                        "precipitation": hourly.get('precip', 0),  # Handling missing values
                        "windspeed": hourly['windspeed'],
                    }
            print("No data available for the specified time.")
            return None
        else:
            print(f"Error: Unable to fetch data. Status code {response.status_code}")
            return None
    def getLocationCoords(self, stadium_name: str):
        location = nflscraper.__loc.geocode(stadium_name)
        # if there is an issue, then it likely has to do with the stadium name, so we'll keep City + state
        while location is None and len(stadium_name) > 0:
            stadium_name = ' '.join(stadium_name.split()[1:])
            location = nflscraper.__loc.geocode(stadium_name)
        if len(stadium_name) <= 0:
            print("Couldn't find lat/lon")
            sys.exit()
        return location.latitude, location.longitude
    def events_list(self, year: int) -> dict:
        return requests.get(self.__event_api_string(year)).json()["events"]
    def interpret_boxscore(self, event, game) -> dict:
        api_boxscore = requests.get(self.__boxscore_api_string(event)).json()["boxscore"]
        boxscore = {}
        # TODO: CAPTURE PLAYER DATA
        for player_data in api_boxscore.get("players", []):
            team_id = player_data.get("team", {}).get("id")
            for stat_category in player_data.get("statistics", []):
                cat_name = stat_category.get("name")
                keys = stat_category.get("keys", [])
                for athlete in stat_category.get("athletes", []):
                    athlete_id = athlete.get("athlete", {}).get("id")
                    stats = athlete.get("stats", [])
                    if athlete_id not in boxscore: 
                        boxscore[athlete_id] = {"team_id": team_id}
                    boxscore[athlete_id].update(dict(zip(keys, stats)))
        home_3rd_eff = api_boxscore["teams"][0]["statistics"][4]["displayValue"].split("-")
        away_3rd_eff = api_boxscore["teams"][1]["statistics"][4]["displayValue"].split("-")
        game["home_third_dwn_pct"] = safe_float_conversion(home_3rd_eff[0]) / safe_float_conversion(home_3rd_eff[1])
        game["away_third_dwn_pct"] = safe_float_conversion(away_3rd_eff[0]) / safe_float_conversion(away_3rd_eff[1])
        home_time_possession = api_boxscore["teams"][0]["statistics"][24]["displayValue"].split(":")
        away_time_possession = api_boxscore["teams"][1]["statistics"][24]["displayValue"].split(":")
        game["home_time_possession"] = safe_float_conversion(home_time_possession[0]) + safe_float_conversion(home_time_possession[1]) / 60.0
        game["away_time_possession"] = safe_float_conversion(away_time_possession[0]) + safe_float_conversion(away_time_possession[1]) / 60.0
        return boxscore
    def get_team(self, id) -> list[dict]:
        team = {}
        data = requests.get(self.__team_api_string(id)).json()["team"]
        team["id"] = int(data["id"])
        team["name"] = data["name"]
        team["display_name"] = data["displayName"]
        team["conference"] = nflscraper.__division[int(data["groups"]["id"][0])][0]
        team["division"] = nflscraper.__division[int(data["groups"]["id"][0])][1]
        team["logo"] = data["logos"][0]["href"]
        team["color"] = data["color"]
        return team
    def get_player(self, player_id):
        pass
    def __athlete_api_string(self, season, player_id) -> str:
        return f"http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{season}/athletes/{player_id}?lang=en&region=us"
    def __team_api_string(self, team_id) -> str:
        return f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team_id}"
    def __boxscore_api_string(self, event) -> str:
        return f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={event}"
    def __event_api_string(self, year: int) -> str:
        return f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates={year}"
    def extract_game_attributes(self, espn_event: dict) -> dict:
        game = {
            "id": int(espn_event["id"]),
            "gameday": datetime.fromisoformat(espn_event["date"]).strftime("%Y-%m-%d"),
            "stadium": espn_event["competitions"][0]["venue"]["fullName"],
            "city": espn_event["competitions"][0]["venue"]["address"]["city"],
            "state": espn_event["competitions"][0]["venue"]["address"].get("state", None),
            "home_team_id": int(espn_event["competitions"][0]["competitors"][0]["id"]),
            "home_team_name": espn_event["competitions"][0]["competitors"][0]["team"]["name"],
            "home_team_display_name": espn_event["competitions"][0]["competitors"][0]["team"]["displayName"],
            "home_score": int(espn_event["competitions"][0]["competitors"][0]["score"]),
            "away_team_id": int(espn_event["competitions"][0]["competitors"][1]["id"]),
            "away_team_name": espn_event["competitions"][0]["competitors"][1]["team"]["name"],
            "away_team_display_name": espn_event["competitions"][0]["competitors"][1]["team"]["displayName"],
            "away_score": int(espn_event["competitions"][0]["competitors"][1]["score"]),
            # missing elo, win pct
            # 3rd down pct added from box score
            # time possession added from box score
            "time": datetime.fromisoformat(espn_event["date"]).strftime("%H:%M"),
            "season": int(espn_event["season"]["year"]),
            "week": int(espn_event["week"]["number"])
        }
        # increase the week number for post season games since espn restarts week count in the post season
        if(int(espn_event["season"]["type"]) == 3): 
            game["week"] += 18 if game["season"] >= 2021 else 17
        # compute the latitude and longitude of the game to obtain weather data
        locationName = f"{game['stadium']} {game['city']} {'' if game['state'] is None else game['state']}"
        game["lat"], game["lon"] = self.getLocationCoords(locationName)
        return game
    def rowify_player(self, game_id: int, player_id: int, player: dict) -> dict:
        row = {
            "player": player_id,
            "game": game_id,
        }
        for stat in player:
            # TODO: Fix sacks
            match stat:
                # written in order of definition in the ddl file
                case "completions/passingAttempts": # written as int/int
                    row["passCompletions"] = safe_float_conversion(player[stat].split("/")[0])
                    row["passAttempts"] = safe_float_conversion(player[stat].split("/")[1])
                case "fieldGoalsMade/fieldGoalAttempts":
                    row["fieldGoalsMade"] = safe_float_conversion(player[stat].split("/")[0])
                    row["fieldGoalAttempts"] = safe_float_conversion(player[stat].split("/")[1])
                case "extraPointsMade/extraPointAttempts":
                    row["extraPointsMade"] = safe_float_conversion(player[stat].split("/")[0])
                    row["extraPointAttempts"] = safe_float_conversion(player[stat].split("/")[1])
                case "interceptions":
                    # check for neighboring keys to indicate if this is an offensive or defensive interception
                    if "QBRating" in player: # offensive interception
                        row["interceptsThrown"] = safe_float_conversion(player[stat])
                    else: # defensive interception
                        row[stat] = safe_float_conversion(player[stat])
                case "sacks-sackYardsLost":
                    row["sackYardsLost"] = safe_float_conversion(player[stat])
                case "team_id": # this doesn't go in the row
                    continue
                case _: 
                    row[stat] = safe_float_conversion(stat)
        return row
    def rowify_game(self, game, weather):
        game = game | weather
        game_fields = ["id", "gameday", "stadium", "city", "state",
                       "home_team_id", "home_score", "home_win_pct",
                       "home_elo", "home_time_possession", "home_third_dwn_pct",
                       "away_team_id", "away_score", "away_win_pct",
                       "away_elo", "away_time_possession", "away_third_dwn_pct",
                       "temperature", "precipitation", "season", "week", "windspeed"]
        return {key: game[key] for key in game if key in game_fields}

def generateInsertStatement(table, obj):
    keys = ', '.join(obj.keys())
    values = ', '.join([f"'{str(value)}'" if isinstance(value, str) else str(value) for value in obj.values()])
    return f"INSERT INTO {table} ({keys}) VALUES ({values});"
def main():
    # set up database
    load_dotenv()

    conn = psycopg2.connect(
        database=os.getenv("NFL_DB_NAME"),
        host=os.getenv("NFL_DB_HOST"),
        user=os.getenv("NFL_DB_USER"),
        password=os.getenv("NFL_DB_PASS"),
        port=os.getenv("NFL_DB_PORT"))
    cursor = conn.cursor()

    # get all teams, a great way to test out the connection before we start also
    cursor.execute("select id from team")
    team_ids = cursor.fetchall()
    ns = nflscraper()
    print(f"Getting NFL data for {year}")
    events = ns.events_list(year)
    for event in events:
        # gather the data from the api
        game = ns.extract_game_attributes(event)
        weather = ns.get_weather_by_coordinates(game["lat"], game["lon"], game["gameday"], game["time"])
        boxscore = ns.interpret_boxscore(game["id"], game)
        # check if the team is in the DB, if not, we'll need to add it. 
        if(game["home_team_id"] not in team_ids):
            cursor.execute(generateInsertStatement("team", ns.get_team(game["home_team_id"])))
        if(game["away_team_id"] not in team_ids):
            cursor.execute(generateInsertStatement("team", ns.get_team(game["away_team_id"])))
        # insert the data into the db
        game_stats = ns.rowify_game(game, weather)
        cursor.execute(generateInsertStatement("game", game_stats))
        player_game_stats = []
        for player in boxscore:
            player_game_stats.append(ns.rowify_player(game["id"], player, boxscore[player]))
            cursor.execute(generateInsertStatement("gameplayer", player_game_stats[-1:][0]))
        cursor.commit()
        if game["home_team_id"] not in team_ids: team_ids.append(game["home_team_id"])
        if game["away_team_id"] not in team_ids: team_ids.append(game["away_team_id"])
        print(f"Gathered {len(player_game_stats)} boxscores for game id {game['id']}")
    conn.close()

if __name__ == "__main__":
    main()
    sys.exit()
