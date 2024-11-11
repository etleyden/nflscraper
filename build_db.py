import sys, json, requests
from datetime import datetime
from geopy.geocoders import Nominatim
import warnings
from dotenv import load_dotenv
import os



if len(sys.argv) > 1:
    year = sys.argv[1]
else:
    print(f"Usage: python build_db.py [YEAR]")
    sys.exit()

def main():
    print(f"Getting NFL data for {year}")
    events = nflscraper.events_list(year)
    for event in events:
        game = extract_game_attributes(event)
        #weather = nflscraper.get_weather_by_coordinates(game["lat"], game["lon"], game["date"], game["time"])
        
        # extract game summary


def extract_game_attributes(espn_event: dict) -> dict:
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
    if(int(espn_event["season"]["type"]) == 3): game["week"] += 18 if game["season"] >= 2021 else 17
    # compute the latitude and longitude of the game to obtain weather data
    locationName = f"{game['stadium']} {game['city']} {"" if game["state"] is None else game["state"]}"
    game["lat"], game["lon"] = nflscraper.getLocationCoords(locationName)
    return game

class nflscraper:
    __loc = Nominatim(user_agent="GetLoc")
    # Load environment variables from .env file
    load_dotenv()
    warnings.filterwarnings("ignore", category=FutureWarning)
    def get_weather_by_coordinates(lat, lon, date, time):
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
        timestamp = int(datetime_obj.timestamp())  # Convert datetime to Unix timestamp
        
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
    def getLocationCoords(stadium_name: str):
        location = nflscraper.__loc.geocode(stadium_name)
        # if there is an issue, then it likely has to do with the stadium name, so we'll keep City + state
        while location is None and len(stadium_name) > 0:
            stadium_name = ' '.join(stadium_name.split()[1:])
            location = nflscraper.__loc.geocode(stadium_name)
        if len(stadium_name) <= 0:
            print("Couldn't find lat/lon")
            sys.exit()
        return location.latitude, location.longitude
    def events_list(year: int) -> dict:
        return requests.get(nflscraper.__event_api_string(year)).json()["events"]
    def interpret_boxscore(event) -> dict:
        boxscore = requests.get(nflscraper.__boxscore_api_string(event)).json()["boxscore"]
        for team in boxscore["players"]:
            team_id = team["team"]["id"]
            for stat in team["statistics"]:
                stat_name = stat["name"]
                
    def __boxscore_api_string(event) -> str:
        return f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={event}"
    def __event_api_string(year: int) -> str:
        return f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates={year}"


if __name__ == "__main__":
    main()
    sys.exit()