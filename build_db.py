import sys, json, requests
from datetime import datetime
from geopy.geocoders import Nominatim
import warnings
from dotenv import load_dotenv
import os
import pandas as pd


if len(sys.argv) > 1:
    year = int(sys.argv[1])
else:
    print("Usage: python build_db.py [YEAR]")
    sys.exit()

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
            print(data)
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
    def interpret_boxscore(self, event) -> dict:
        api_boxscore = requests.get(self.__boxscore_api_string(event)).json()["boxscore"]
        boxscore = {}
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
        return boxscore
    def get_teams(self) -> list[dict]:
        teams = []
        for i in range(1, 35):
            team = {}
            data = requests.get(self.__team_api_string(i)).json()["team"]
            team["id"] = int(data["id"])
            team["name"] = data["name"]
            team["display_name"] = data["displayName"]
            team["conference"] = nflscraper.__division[int(data["groups"]["id"][0])]
            team["division"] = nflscraper.__division[int(data["groups"]["id"][1])]
            team["logo"] = data["logos"][0]["href"]
            team["color"] = data["color"]
            teams.append(team)
        return teams
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
            "home_score": int(espn_event["competitions"][0]["competitors"][0]["score"]),
            "away_score": int(espn_event["competitions"][0]["competitors"][1]["score"]),
            "home_team_id": int(espn_event["competitions"][0]["competitors"][0]["id"]),
            "away_team_id": int(espn_event["competitions"][0]["competitors"][1]["id"]),
            "home_team_name": espn_event["competitions"][0]["competitors"][0]["team"]["displayName"],
            "away_team_name": espn_event["competitions"][0]["competitors"][1]["team"]["displayName"],
            "stadium": espn_event["competitions"][0]["venue"]["fullName"],
            "city": espn_event["competitions"][0]["venue"]["address"]["city"],
            "state": espn_event["competitions"][0]["venue"]["address"].get("state", None),
            "date": datetime.fromisoformat(espn_event["date"]).strftime("%Y-%m-%d"),
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


def main():
    ns = nflscraper()
    print(f"Getting NFL data for {year}")
    events = ns.events_list(year)
    game_columns = ["id", "gameday", "city", "state", "home_team", "home_score",
        "home_win_pct", "home_elo", "home_time_possession", "home_third_dwn_pct", 
        "away_team", "away_score", "away_win_pct", "away_elo", "away_time_possession", 
        "away_third_down_pct", "temp", "precipitation", "season", "week"]
    boxscore_identifying_cols = ["game_id", "player_id"]
    boxscore_columns = ["pass_attempts", "pass_completions", "receptions", "fumbles", "intercepts_thrown", 
            "receive_yds", "rush_yds", "pass_yds", "pass_tds", "rush_tds", "targets", "receive_tds", "rush_attempts", 
            "qbr", "interceptions", "fumble_recoveries", "sacks", "tackles", "defensive_tds", "punts", "punt_yds", 
            "punt_return_yds", "punt_returns", "kicks", "kick_return_yds", "kick_returns", "kick_return_tds", "field_goal_attempts", 
            "field_goal_makes_20", "field_goal_makes_30", "field_goal_makes_40", "field_goal_makes_50", "xtra_pt_attempts",
            "xtra_pt_completions"]
    games = pd.DataFrame(game_columns)
    boxscores = pd.DataFrame(boxscore_identifying_cols + boxscore_columns)
    for event in events:
        #game = ns.extract_game_attributes(event)
        #weather = ns.get_weather_by_coordinates(game["lat"], game["lon"], game["date"], game["time"])
        #boxscore = ns.interpret_boxscore(game["id"])
        # TODO: convert boxscore and game to correct format for db
        # extract game summary
        
        
        
        

def extract_game_attributes(ns: nflscraper, espn_event: dict) -> dict:
    game = {
        "id": int(espn_event["id"]),
        "home_score": int(espn_event["competitions"][0]["competitors"][0]["score"]),
        "away_score": int(espn_event["competitions"][0]["competitors"][1]["score"]),
        "home_team_id": int(espn_event["competitions"][0]["competitors"][0]["id"]),
        "away_team_id": int(espn_event["competitions"][0]["competitors"][1]["id"]),
        "home_team_name": espn_event["competitions"][0]["competitors"][0]["team"]["displayName"],
        "away_team_name": espn_event["competitions"][0]["competitors"][1]["team"]["displayName"],
        "stadium": espn_event["competitions"][0]["venue"]["fullName"],
        "city": espn_event["competitions"][0]["venue"]["address"]["city"],
        "state": espn_event["competitions"][0]["venue"]["address"].get("state", None),
        "date": datetime.fromisoformat(espn_event["date"]).strftime("%Y-%m-%d"),
        "time": datetime.fromisoformat(espn_event["date"]).strftime("%H:%M"),
        "season": int(espn_event["season"]["year"]),
        "week": int(espn_event["week"]["number"])
    }
    # increase the week number for post season games since espn restarts week count in the post season
    if(int(espn_event["season"]["type"]) == 3): 
        game["week"] += 18 if game["season"] >= 2021 else 17
    # compute the latitude and longitude of the game to obtain weather data
    locationName = f"{game['stadium']} {game['city']} {'' if game['state'] is None else game['state']}"
    game["lat"], game["lon"] = ns.getLocationCoords(locationName)
    return game


if __name__ == "__main__":
    main()
    sys.exit()
