SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS player, team, position, playerteam, injury, precipitation, game, gameplayer
SET FOREIGN_KEY_CHECKS=1;


# this will include coaches
CREATE TABLE player (
    id int PRIMARY KEY,
    name varchar(30)
)

CREATE TABLE team(
    id int PRIMARY KEY,
    name varchar(30)
)

CREATE TABLE position(
    id int PRIMARY KEY,
    name varchar(20)
)
CREATE TABLE playerteam(
    team_id int,
    player_id int,
    start date,
    end date,
    position int,
    PRIMARY KEY(player_id, start),
    FOREIGN KEY (team_id) REFERENCES team(id),
    FOREIGN KEY (player_id) REFERENCES player(id)
)

CREATE TABLE injury(
    player_id int,
    season int,
    week int,
    PRIMARY KEY (player_id, season, week),
    FOREIGN KEY (player_id) REFERENCES player(id)
)

CREATE TABLE precipitation(
    id int PRIMARY KEY,
    name varchar(15)
)

CREATE TABLE game(
    id int PRIMARY KEY,
    gameday date,
    city varchar(20),
    state char(2),
    # home team stats
    home_team int,
    home_score int,
    home_win_pct float,
    home_elo float,
    home_time_possession int,
    home_third_dwn_pct float,
    #away team stats
    away_team int,
    away_score int,
    away_win_Pct float,
    away_elo float,
    away_time_possession int,
    away_third_dwn_pct float,
    # weather + and season info
    temp int,
    precipitation int,
    season int,
    week int,
    FORIEGN KEY (home_team) REFERENCES team(id),
    FOREIGN KEY (away_team) REFERENCES team(id),
    FOREIGN KEY (precipitation) REFERENCES precipitation(id)
)

CREATE TABLE gameplayer(
    game int,
    player int,
    FOREIGN KEY (game) REFERENCES game(id),
    FOREIGN KEY (player) REFERENCES player(id)
    # offense stats
    pass_attempts int,
    pass_completion int,
    receptions int,
    fumbles int,
    intercepts_thrown int,
    receive_yds int,
    pass_yds int,
    rush_yds int,
    pass_yds int,
    pass_tds int,
    rush_tds int,
    targets int,
    receive_tds int,
    rush_attempts int,
    qbr int,
    # defense stats
    interceptions int,
    fumble_recoveries int,
    sacks int,
    tackles int,
    defensive_tds int,
    # special
    punts int,
    punt_yds int,
    punt_return_yds int,
    punt_returns int,
    kicks int,
    kick_return_yds int,
    kick_returns int,
    kick_return_tds int,
    field_goal_attempts int,
    field_goal_makes_20 int,
    field_goal_makes_30 int,
    field_goal_makes_40 int,
    field_goal_makes_50 int,
    xtra_pt_attempts int,
    xtra_pt_completions int
)