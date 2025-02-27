"""
============================
===      build_db.py     ===
===     Ethan Leyden     ===
============================
usage: python build_db.py [YEAR] [optional ignore_date]
ignore_date: YYYY-MM-DD
"""
import sys, json, requests, warnings, os, re, time
import psycopg2, pprint
from tqdm import tqdm
from datetime import datetime
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
from bs4 import BeautifulSoup as bs
import pandas as pd

def safe_float_conversion(value):
    try:
        return float(value)
    except (ValueError, TypeError) as err:
        #print(err)
        return 0.0
    
class nflscraper():
    __loc = Nominatim(user_agent="GetLoc") # Library for getting coordinates from a place name
    __division = { # dictionary to look up divisions and conferences based on ESPN team "parent"
        12: ["AFC", "N"],
        13: ["AFC", "S"],
        4: ["AFC", "E"],
        6: ["AFC", "W"],
        10: ["NFC", "N"],
        11: ["NFC", "S"],
        1: ["NFC", "E"],
        3: ["NFC", "W"],
    }
    # TODO: fix the weather situation to reduce weather precipitation down to ~5 severity levels or maybe even fewer
    __descriptors = [ # dictionary to assign weather descriptors to a predefined ranking.
        # these descriptors are based on nflweather.com, the source for our weather data
        # they do not match, but the listed descriptor will be reduced to one of these based on matching
        "sun", "fair", "clear", "cloud", "overcast", "humid", "fog", "drizzle", "rain", "thunderstorms", "snow"
        # these could be reduced further in preprocessing
    ]
    __descriptors_v2 = {
        1: ["sun", "fair", "clear"],
        2: ["cloud", "overcast", "humid", "fog", "drizzle"],
        3: ["rain", "thunderstorms"],
        4: ["snow"]
    }
    # Load environment variables from .env file
    load_dotenv()
    warnings.filterwarnings("ignore", category=FutureWarning)
    def __init__(self, cursor=None):
        # TODO: potentially move this to build_db class in generate_csv.py if it improves decoupling and cohesion
        # this is where we set up __descriptors
        if cursor is not None:
            # create the dictionary from the db, else use the default
            self.__descriptors = nflscraper.load_descriptors(cursor)
        else:
            # just in case someone is running an old version of the db. 
            self.__descriptors = self.__descriptors_v2

        return
    def get_descriptors_v2():
        return nflscraper.__descriptors_v2
    def load_descriptors(cursor) -> dict:
        # create the dictionary from the db, else use the default
        cursor.execute("select * from precipitation");
        precipitation = cursor.fetchall()
        descriptors = {}
        for i in precipitation:
            if i[2] not in descriptors:
                descriptors[i[2]] = []
            descriptors[i[2]].append(i[1])
        return descriptors
    def get_weather_by_game(self, home, away, season, week):
        # handle pre/postseason games. an unusual week number will indicate what "special week" it is
        if week >= 18 and season <= 2020: week += 1
        # handle commanders name changes
        if season > 2020:
            if home == "Commanders": home = "Washington"
            elif away == "Commanders": away = "Washington"
        elif season == 2020:
                if home == "Washington" and (week < 12 or week == 15): home = "football%20team" if week > 2 else "redskins"
                elif away == "Washington" and (week < 12 or week == 15): away = "football%20team" if week > 2 else "redskins"
        else:
            if home == "Washington": home = "redskins"
            elif away == "Washington": away = "redskins"
        # handle non-regular season games
        if week > 18 and season < 2023:
            match(week):
                case 19: week = "wildcard-weekend"
                case 20: week = "divisional-playoffs"
                case 21: week = "%20conf-championships" if season > 2018 else "conf-championships"
                case 23: week = "superbowl"
        elif week > 18 and season >= 2023:
            match(week):
                case 19: week = "wild-card"
                case 20: week = "conference-championship"
        elif week < 0 and season >= 2023:
            match(week):
                case -1: week = "preseason-week-3"
                case -2: week = "preseason-week-2"
                case -3: week = "preseason-week-1"
                case -4: week = "hall-of-fame-weekend"
        elif week <= 0:
            match(week):
                case 0: week = "pre-season-week-4"
                case -1: week = "pre-season-week-3"
                case -2: week = "pre-season-week-2"
                case -3: week = "pre-season-week-1"
                case -4: week = "pre-season-week-1"
        else: week = f"week-{week}"
        # clean home/away strings so they match team names
        home, away = home.split()[-1], away.split()[-1]
        url = f"https://www.nflweather.com/games/{season}/{week}/{away}-at-{home}"
        response = requests.get(url)
        if response.status_code >= 400: # if there was an issue getting the weather data, we'll terminate.
            print(f"HTTP Error: {response.status_code}")
            print(away, home, season, week, "|", url)
            print(response.content)
            sys.exit(1)

        # turn the HTML blob into single-space separated textual content
        response = re.sub(r"\s+", " ", bs(str(response.content), 'html.parser').get_text().replace("\\n", ""))
        # temps are the first number after "Kickoff", "Q2", "Q3", "Q4"
        # Quarter [Weather] [Temp] 
        weather = re.findall(r"(Kickoff|Q2|Q3|Q4)\s([a-zA-Z|\s]*)([0-9]{1,3})", response)
        if len(weather) == 0: # didn't grab any weather data
            print("Unable to parse nflweather page for this game:")
            print(away, home, season, week, "|", url)
            print(response)
            return {}
            
        weather = [(i[0], i[1].strip().lower(), int(i[2])) for i in weather] # clean the strings
        temp = sum([i[2] for i in weather]) / len(weather) # average temperature
        # "worst" weather descriptor
        descriptor = None

        # ==== BEGIN REPLACE
        # TODO: Question complexity of the following four lines?
        # match to the descriptor with the worst severity
        for severity_level in self.__descriptors_v2: # for each of the severity levels
            for predefined_desc in self.__descriptors_v2[severity_level]: # for each of the descriptors in that severity level
                for scraped_desc in weather:
                    if predefined_desc in scraped_desc[1]: 
                        descriptor = severity_level
        # match to the one of the last quarter
        if descriptor is None: 
            descriptor = weather[-1:]
        # ==== END REPLACE

        # ==== BEGIN REMOVE (commented out until I can verify that the new method works, delete upon verification)
        # for d in self.__descriptors: # for each of the possible descriptors
        #     for w in weather: # for weather in each of the 4 quarters
        #         if d in w[1]: descriptor = d # if its later in the list, it is more severe
        # if descriptor is None:
        #     for d in self.__descriptors:
        #         for w in weather:
        #             print(f"{d} | {w} | {d in w}")
        #     print(f"Could not match descriptor for {[w[1] for w in weather]}")
        # ==== END REMOVE

        # TODO: grab windspeed
        return {"temperature": temp, "precipitation": descriptor}
    # ==== DEPRECATED ????? ====
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
            if response.status == 429:
                print("Out of API calls for weather. Try again later.")
            else:
                print(f"Error: Unable to fetch data. Status code {response.status_code}")
            return None
    def getLocationCoords(self, stadium_name: str):
        attempts = 0
        while attempts < 3:
            if attempts > 0: print("Querying coords...", end="")
            try:
                location = nflscraper.__loc.geocode(stadium_name)
                # if there is an issue, then it likely has to do with the stadium name, so we'll keep City + state
                while location is None and len(stadium_name) > 0:
                    stadium_name = ' '.join(stadium_name.split()[1:])
                    location = nflscraper.__loc.geocode(stadium_name)
                if len(stadium_name) <= 0:
                    print("Couldn't find lat/lon")
                    sys.exit()
                if attempts > 0: print("Success!")
                attempts = 99
            except Exception as err:
                print(str(err))
                time.sleep(1)
                attempts += 1
                if attempts == 3: return None, None
        return location.latitude, location.longitude
    def events_list(self, year: int) -> dict:
        return requests.get(self.__event_api_string(year)).json()["events"]
    def interpret_boxscore(self, event, game) -> dict:
        """
        Returns a list of players, with their corresponding statistics based on the boxscore object for that game, as well as a dictionary containing athlete_id: name pairs to
        streamline the population of the players table
        """
        api_boxscore = requests.get(self.__boxscore_api_string(event)).json()["boxscore"]
        players = {}
        boxscore = {}
        # TODO: CAPTURE PLAYER DATA like name, team history, etc.
        for player_data in api_boxscore.get("players", []):
            team_id = player_data.get("team", {}).get("id")
            for stat_category in player_data.get("statistics", []):
                cat_name = stat_category.get("name")
                keys = stat_category.get("keys", [])
                for athlete in stat_category.get("athletes", []):
                    athlete_id = int(athlete.get("athlete", {}).get("id"))
                    athlete_name = athlete.get("athlete", {}).get("displayName", "")
                    stats = athlete.get("stats", [])
                    if athlete_id not in boxscore: 
                        boxscore[athlete_id] = {"team_id": team_id}
                    boxscore[athlete_id].update(dict(zip(keys, stats)))
                    if athlete_id not in players:
                        players[int(athlete_id)] = athlete_name
        home_3rd_eff = api_boxscore["teams"][0]["statistics"][4]["displayValue"].split("-")
        away_3rd_eff = api_boxscore["teams"][1]["statistics"][4]["displayValue"].split("-")
        try:
            game["home_third_dwn_pct"] = safe_float_conversion(home_3rd_eff[0]) / safe_float_conversion(home_3rd_eff[1])
        except ZeroDivisionError as err:
            game["home_third_dwn_pct"] = 0.0
        try:
            game["away_third_dwn_pct"] = safe_float_conversion(away_3rd_eff[0]) / safe_float_conversion(away_3rd_eff[1])
        except ZeroDivisionError as err:
            game["away_third_dwn_pct"] = 0.0
        home_time_possession = api_boxscore["teams"][0]["statistics"][24]["displayValue"].split(":")
        away_time_possession = api_boxscore["teams"][1]["statistics"][24]["displayValue"].split(":")
        game["home_time_possession"] = safe_float_conversion(home_time_possession[0]) + safe_float_conversion(home_time_possession[1]) / 60.0
        game["away_time_possession"] = safe_float_conversion(away_time_possession[0]) + safe_float_conversion(away_time_possession[1]) / 60.0
        return boxscore, players
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
            "home_team_name": espn_event["competitions"][0]["competitors"][0]["team"]["name" if int(espn_event["season"]["year"]) >= 2023 else "shortDisplayName"],
            "home_team_display_name": espn_event["competitions"][0]["competitors"][0]["team"]["displayName"],
            "home_score": int(espn_event["competitions"][0]["competitors"][0]["score"]),
            "away_team_id": int(espn_event["competitions"][0]["competitors"][1]["id"]),
            "away_team_name": espn_event["competitions"][0]["competitors"][1]["team"]["name" if int(espn_event["season"]["year"]) >= 2023 else "shortDisplayName"],
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
        # decrease the week number of pre-season games (negative number)
        elif(int(espn_event["season"]["type"]) == 1):
            game["week"] -= 5 # on the nflweather, hall-of-game-weekend is grouped with preseason week 1
        # compute the latitude and longitude of the game to obtain weather data
        locationName = f"{game['stadium']} {game['city']} {'' if game['state'] is None else game['state']}"
        game["lat"], game["lon"] = self.getLocationCoords(locationName)
        return game
    def rowify_player(self, game_id: int, player_id: int, player: dict) -> dict:
        row = {
            "player": int(player_id),
            "game": int(game_id),
        }
        for stat in player:
            if stat.startswith("long"): continue
            # TODO: Fix sacks < new note: What did I mean by this??
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
                    row["team"] = int(player[stat])
                case _: 
                    row[stat] = safe_float_conversion(player[stat])
        return row
    def rowify_game(self, game, weather):
        if weather is not None:
            game = game | weather
        game_fields = ["id", "gameday", "stadium", "city", "state",
                       "home_team_id", "home_score", "home_win_pct",
                       "home_elo", "home_time_possession", "home_third_dwn_pct",
                       "away_team_id", "away_score", "away_win_pct",
                       "away_elo", "away_time_possession", "away_third_dwn_pct",
                       "temperature", "precipitation", "season", "week", "windspeed"]
        return {key: game[key] for key in game if (key in game_fields) and (game[key] is not None)}
    def test_boxscores(self):
        events = self.events_list(2023)
        game = self.extract_game_attributes(events[0])
        boxscore, players = self.interpret_boxscore(game['id'], game)
        pprint.pp(boxscore[3116188])
        pprint.pp(self.rowify_player(game['id'], 3116188, boxscore[3116188]))



def generateInsertStatement(table, obj):
    keys = ', '.join(obj.keys())
    values = ', '.join([f"\'{str(value).replace('\'', '\'\'')}\'" if isinstance(value, str) else str(value) for value in obj.values()])
    return f"""INSERT INTO {table} ({keys}) VALUES ({values});"""

def main():
    missing_weather = []
    num_games = 0
    if len(sys.argv) > 1:
        year = int(sys.argv[1])
        # ignore all events with an ID less than the given optional argument
        ignore_prior_to = datetime.strptime(sys.argv[2], "%Y-%m-%d").date() if len(sys.argv) > 2 else None
    else:
        print("Usage: python build_db.py [YEAR] [optional -- eventID]\nAn eventID argument will tell the scraper to ignore all events with an ID less than the one given")
        sys.exit()
    # set up database
    load_dotenv()

    conn = psycopg2.connect(
        database=os.getenv("NFL_DB_NAME"),
        host=os.getenv("NFL_DB_HOST"),
        user=os.getenv("NFL_DB_USER"),
        password=os.getenv("NFL_DB_PASS"),
        port=os.getenv("NFL_DB_PORT"))
    cursor = conn.cursor()

    # get all entities already existing 
    cursor.execute("select id from team")
    team_ids = [team[0] for team in cursor.fetchall()]
    cursor.execute("select id from player")
    player_ids = [player[0] for player in cursor.fetchall()]
    cursor.execute("select id from game")
    game_ids = [game[0] for game in cursor.fetchall()]
    ns = nflscraper(cursor=cursor)
    print(f"Getting NFL data for {year}")
    events = ns.events_list(year)
    haveSkipped = False
    progress_bar = tqdm(total = len(events), desc="Processing events...", ncols = 100)
    statusline = tqdm(total = 0, position=1, bar_format='{desc}')
    for idx, event in enumerate(events):
        # see if event is before specified date
        if ignore_prior_to is not None and datetime.strptime(event["date"], "%Y-%m-%dT%H:%MZ").date() <= ignore_prior_to:
            if not haveSkipped: # pretty print the list of skipped games
                print("Skipping", end=" ")
                haveSkipped = True
            print(event["id"], end=", ")
            continue
        elif haveSkipped: 
            haveSkipped = False
            print()

        # check if the game is the pro bowl -- no impact on super bowl
        if (event["shortName"] == "AFC VS NFC" or 
            event["shortName"] == "NFC VS AFC" or 
            "IRV" in event["shortName"] or # rice and irvine are popular team names to choose for the pro bowl
            "RIC" in event["shortName"]): 
                continue

        # gather the data from the api
        try:
            game = ns.extract_game_attributes(event)
        except KeyError as err:
            print(err)
            print(event)
            sys.exit(1)

        weather = ns.get_weather_by_game(game["home_team_name"], game["away_team_name"], game["season"], game["week"])
        if not weather:
            missing_weather.append(game["id"])
        boxscore, players = ns.interpret_boxscore(game["id"], game)
        
        # Add any new players to the players table
        new_athletes = 0
        for athlete in players.keys():
            if athlete not in player_ids:
                new_athletes += 1
                cursor.execute(generateInsertStatement("player", {"id": athlete, "name": players[athlete]}))
                player_ids.append(athlete)
        if new_athletes > 0: conn.commit()

        # check if the team is in the DB, if not, we'll need to add it. 
        if(game["home_team_id"] not in team_ids):
            cursor.execute(generateInsertStatement("team", ns.get_team(game["home_team_id"])))
            conn.commit()
            team_ids.append(game["home_team_id"])
        if(game["away_team_id"] not in team_ids):
            cursor.execute(generateInsertStatement("team", ns.get_team(game["away_team_id"])))
            conn.commit()
            team_ids.append(game["away_team_id"])

        # insert the game into the db
        game_stats = ns.rowify_game(game, weather)
        if(game["id"] not in game_ids):
            try:
                cursor.execute(generateInsertStatement("game", game_stats))
            except psycopg2.errors.UndefinedColumn as err:
                print(generateInsertStatement("game", game_stats))
                print(err)
                sys.exit(1)
            except psycopg2.errors.SyntaxError as err:
                print(generateInsertStatement("game", game_stats))
                print(err)
                sys.exit(1)
            conn.commit()
            game_ids.append(game["id"])
        
        # insert the boxscore for all players who played in that game
        player_game_stats = []
        cursor.execute("select game, player from gameplayer")
        gameplayer_ids = cursor.fetchall()
        for player in boxscore:
            # all players should be added on line 251 --> What did I mean by this?

            # convert the boxscore for this player at this game into a writeable row, and write it
            player_game = ns.rowify_player(game["id"], player, boxscore[player])
            if (player_game["game"], player_game["player"]) not in gameplayer_ids:
                cursor.execute(generateInsertStatement("gameplayer", player_game))
                player_game_stats.append(player_game)
        conn.commit()
        if game["home_team_id"] not in team_ids: team_ids.append(game["home_team_id"])
        if game["away_team_id"] not in team_ids: team_ids.append(game["away_team_id"])
        num_games += 1
        progress_bar.update(1)
        statusline.set_description_str(f"{idx} | Game {game['id']} (Week {game['week']} | {game['away_team_name']} at {game['home_team_name']}) on [{game['gameday']}]: {len(player_game_stats)} boxscores.")
    conn.close()
    print(f"Collected data for {num_games} games, missing weather data for: {missing_weather}")

if __name__ == "__main__":
    main()
    sys.exit()
