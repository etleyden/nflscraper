import sys, os, psycopg2, psycopg2.extras, pprint
import pandas as pd
from dotenv import load_dotenv

class nfldb():
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
    def get_n_previous_games(self, game_id, n):
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
    def aggregate_player_data(self, game_id):
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