import sys, os, psycopg2, psycopg2.extras, pprint
import pandas as pd
from dotenv import load_dotenv
from typing import Union

class nfldb():
    __supported_features = ["score"]
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
        return [dict(row) for row in result]
    def aggregate_player_data(self, game_id: int, n_prev_games: int = 5, agg_method: Union[dict, str] = "avg", features: list=__supported_features):
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
        
        previous_games = self.get_n_previous_games(game_id, n_prev_games)

        # Go through each of the features and aggregate them.
        for feature in features:
            match(feature):
                case "score":
                    
                    pass

def main():
    load_dotenv()
    db = nfldb(
        db=os.getenv("NFL_DB_NAME"),
        host=os.getenv("NFL_DB_HOST"),
        user=os.getenv("NFL_DB_USER"),
        password=os.getenv("NFL_DB_PASS"),
        port=os.getenv("NFL_DB_PORT")
    )
    prev_games = db.get_n_previous_games(401547637, 5)
    pprint.pp(prev_games)

if __name__ == "__main__":
    main()
    sys.exit()