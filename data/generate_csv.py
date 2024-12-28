import sys, os, psycopg2, psycopg2.extras, pprint
import pandas as pd
from statistics import mean
from tqdm import tqdm
from dotenv import load_dotenv
from typing import Union

class nfldb():
    __supported_features = {
        "team": ["score", "third_dwn_pct"], # team features will have a home/away stat
        "player": ["qbrating"], # player features will be found in the boxscores
        "game": [] # game statistics will be team-independent (i.e. weather)
    }
    def __init__(self, db, host, user, password, port):
        self.__database = db
        self.__host = host
        self.__user = user
        self.__password = password
        self.__port = port
        try:
            connection = self.__connect() 
            connection.cursor().execute("SELECT 1;")
            connection.commit()
            print("Connection to Database: Valid")
        except Exception as e:
            print("Error connecting to database: {e}")
    def __connect(self):
        return psycopg2.connect(dbname=self.__database, host=self.__host, user=self.__user, password=self.__password, port=self.__port)
    def __filter_by_team(game_list: list[dict], team_id: int, feature: str) -> list:
        """Filter a list of games by team id and return a list of values for a particular feature"""
        result = []
        for game in game_list:
            if game["home_team_id"] == team_id: result.append(game[f"home_{feature}"])
            if game["away_team_id"] == team_id: result.append(game[f"away_{feature}"])
        return result
    def __filter_boxscores_by_team(boxscores: list[dict], home_team_id: int, away_team_id: int, feature: str) -> list:
        """Given a list of boxscores, return two arrays of game-by-game stats for a particular feature.
        Example output: [array of passing yards for every game for home team], [array of passing yards for every game for away team]
        """
        # aggregate results by game
        result = {}
        for boxscore in boxscores:
            #pprint.pp(boxscore)
            if boxscore[feature] is not None:
                game = boxscore['game']
                team = boxscore['team']
                if team not in result: result[team] = {}
                if game not in result[team]: result[team][game] = 0
            
                result[team][game] += boxscore[feature]

        home_stats = []
        away_stats = []
        for game in result[home_team_id]: home_stats.append(result[home_team_id][game])
        for game in result[away_team_id]: away_stats.append(result[away_team_id][game])

        return home_stats, away_stats

    def get_game(self, game_id: int):
        conn = self.__connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(f"""SELECT * FROM game WHERE id = {game_id}""")
        result = cursor.fetchone()
        conn.close()
        return dict(result)
    def get_n_previous_games(self, game_id: int, n: int) -> list[dict]:
        conn = self.__connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(f"""
        WITH 
        game_info AS (
            SELECT gameday, home_team_id, away_team_id FROM game WHERE id = {game_id}
        )
        (SELECT * FROM game WHERE 
            gameday < (SELECT gameday FROM game_info) AND
            (home_team_id = (SELECT home_team_id FROM game_info) 
            OR away_team_id = (SELECT home_team_id FROM game_info))
        LIMIT {n})

        UNION

        (SELECT * FROM game
        WHERE 
            gameday < (SELECT gameday FROM game_info) AND
            (home_team_id = (SELECT away_team_id FROM game_info)
            OR away_team_id = (SELECT away_team_id FROM game_info))
        LIMIT {n});
        """)
        result = cursor.fetchall()
        conn.close()
        return [dict(row) for row in result]
    def get_previous_game_boxscores(self, game_id: int, n: int) -> list[dict]:
        conn = self.__connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(f"""
        WITH 
        game_info AS (
            SELECT gameday, home_team_id, away_team_id FROM game WHERE id = {game_id}
        ),
        prev_games AS ((
            SELECT id FROM game WHERE 
                gameday < (SELECT gameday FROM game_info) AND
                (home_team_id = (SELECT home_team_id FROM game_info) 
                OR away_team_id = (SELECT home_team_id FROM game_info))
            LIMIT {n})

            UNION

            (SELECT id FROM game
            WHERE 
                gameday < (SELECT gameday FROM game_info) AND
                (home_team_id = (SELECT away_team_id FROM game_info)
                OR away_team_id = (SELECT away_team_id FROM game_info))
            LIMIT {n})
        )
        SELECT * FROM gameplayer WHERE game IN (SELECT id FROM prev_games);
        """)
        result = cursor.fetchall();
        conn.close()
        return [dict(row) for row in result]
    def aggregate_team_data(self, game: dict, n_prev_games: int = 5, agg_method: str = "avg", features: list=__supported_features):
        """Given a game ID, generate a vector for that game based on the event_id

        Args:
            game_id (int): The espn event_id. This is used to identify the game within the local database
            n_prev_games (int): The number of previous games (for each team) to retrieve to generate the 
                vector. In the case where one of those games contains both teams, it will be used for 
                both teams in the resulting vector.
            agg_method (str|dict): The aggregation method used to incorporate statistics about previous 
                games. Passing a string tells applies the aggregation method to all features. Passing a
                dict in the format { "feature": "agg_method" } will apply the given agg_method to a 
                particular feature. The default aggregation method is "avg".
            features (List[str]): The features to extract from the local db.

        Returns:
            List[]: The feature that represents the game, with the last element in the list being 
                the label (0: Home Team won, 1: Away Team won)
        """
        
        game_id = game["id"]
        home_team = game["home_team_id"]
        away_team = game["away_team_id"]

        result = {}

        # TODO: Optimize this function by reducing database reads somehow? 
        # Right now a read is done to get data for previous N games, once 
        # for every game -- a lot of duplicate data being read!
        previous_games = self.get_n_previous_games(game_id, n_prev_games)

        # Go through each of the features and aggregate them.
        for feature in features["team"]:
            match(feature):
                case _:
                    home_stats = nfldb.__filter_by_team(previous_games, home_team, feature)
                    away_stats = nfldb.__filter_by_team(previous_games, away_team, feature)
                    # negative number indicates favor of home team, positive number indicates favor of home team
                    result[feature] = mean(away_stats) - mean(home_stats)
        
        prev_game_boxscores = self.get_previous_game_boxscores(game_id, n_prev_games)

        for feature in features["player"]:
            match(feature):
                case _:
                    home_stats, away_stats = nfldb.__filter_boxscores_by_team(prev_game_boxscores, home_team, away_team, feature)
                    result[feature] = mean(away_stats) - mean(home_stats)
        

        result["game_id"] = game_id
        # Should be switched to -1 / 1
        result["label"] = "Home" if game["home_score"] > game["away_score"] else "Away"

        return result
    def generate_training_data(self, year: int) -> pd.DataFrame:
        # collect a list of all games in the 2023 season
        conn = self.__connect()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(f"""SELECT * FROM game WHERE season={year}""")
        games = cursor.fetchall()
        objects = []
        for game in tqdm(games, desc="Generating Features..."):
            objects.append(self.aggregate_team_data(game))
        conn.close()
        return pd.DataFrame(objects)

def main():
    load_dotenv()
    db = nfldb(
        db=os.getenv("NFL_DB_NAME"),
        host=os.getenv("NFL_DB_HOST"),
        user=os.getenv("NFL_DB_USER"),
        password=os.getenv("NFL_DB_PASS"),
        port=os.getenv("NFL_DB_PORT")
    )
    #prev_games = db.get_n_previous_games(401547637, 5)
    #game = db.get_game(401547637)
    #feature = db.aggregate_data(game)

    #boxscores = db.get_previous_game_boxscores(401547637, 5)

    training = pd.concat([db.generate_training_data(year) for year in range(2022, 2024)])
    training.to_csv("nfl_2023_v1.csv", index=False)

if __name__ == "__main__":
    main()
    sys.exit()