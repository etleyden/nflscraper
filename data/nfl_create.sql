DROP TABLE IF EXISTS player, team, position, playerteam, injury, precipitation, game, gameplayer;

-- this will include coaches
CREATE TABLE player (
    id int PRIMARY KEY,
    name varchar(30)
);

CREATE TABLE team (
    id int PRIMARY KEY,
    name varchar(30) NOT NULL,
    display_name varchar(30),
    conference char(3) NOT NULL,
    division char(1) NOT NULL,
    logo varchar(50),
    color char(6)
);

CREATE TABLE position(
    id int PRIMARY KEY,
    name varchar(20)
);

CREATE TABLE playerteam(
    team_id int,
    player_id int,
    start_date date,
    end_date date,
    position int,
    PRIMARY KEY(player_id, start_date),
    FOREIGN KEY (team_id) REFERENCES team(id),
    FOREIGN KEY (player_id) REFERENCES player(id)
);

CREATE TABLE injury(
    player_id int,
    season int,
    week int,
    PRIMARY KEY (player_id, season, week),
    FOREIGN KEY (player_id) REFERENCES player(id)
);

CREATE TABLE precipitation(
    id int PRIMARY KEY,
    name varchar(15)
);

CREATE TABLE game(
    id int PRIMARY KEY,
    gameday date,
    stadium varchar(50),
    city varchar(50),
    state char(2),
    -- home team stats
    home_team_id int,
    home_score int,
    home_win_pct real,
    home_elo real,
    home_time_possession real,
    home_third_dwn_pct real,
    -- away team stats
    away_team_id int,
    away_score int,
    away_win_pct real,
    away_elo real,
    away_time_possession real,
    away_third_dwn_pct real,
    -- weather + and season info
    temperature real,
    precipitation varchar(20), -- amount of liquid precip or liquid equiv
    windspeed real,
    season int,
    week int,
    FOREIGN KEY (home_team_id) REFERENCES team(id),
    FOREIGN KEY (away_team_id) REFERENCES team(id)
);

CREATE TABLE gameplayer(
    game int,
    player int,
    PRIMARY KEY(game, player),
    FOREIGN KEY (game) REFERENCES game(id),
    FOREIGN KEY (player) REFERENCES player(id),
    -- offense stats
    -- passing    
    passCompletions real,
    passAttempts real,
    passingYards real, 
    yardsPerPassAttempt real,
    passingTouchdowns real,
    interceptsThrown real, 
    sackYardsLost real,
    adjQBR real,
    QBRating real,
    -- rushing
    rushingAttempts real,
    rushingYards real, 
    yardsPerRushAttempt real,
    rushingTouchdowns real,
    longRushing real,
    -- receiving
    receptions real,
    receivingYards real, 
    yardsPerReception real,
    receivingTouchdowns real,
    receivingTargets real,
    -- fumbles
    fumbles real,
    fumblesLost real,
    fumblesRecovered real,
    -- defense stats
    totalTackles real,
    soloTackles real,
    sacks real,
    tacklesForLoss real,
    passesDefended real,
    QBHits real,
    defensiveTouchdowns real,
    -- interceptions (defense)
    interceptions real,
    interceptionYards real,
    interceptionTouchdowns real,
    -- special
    -- kickReturns
    kickReturns real,
    kickReturnYards real,
    yardsPerKickReturn real,
    longKickReturn real,
    kickReturnTouchdowns real,
    -- puntReturns
    puntReturns real,
    puntReturnYards real,
    yardsPerPuntReturn real,
    longPuntReturn real,
    puntReturnTouchdowns real,
    -- kicking
    fieldGoalsMade real,
    fieldGoalAttempts real,
    fieldGoalPct real,
    longFieldGoalMade real,
    extraPointsMade real,
    extraPointAttempts real,
    totalKickingPoints real,
    -- punting
    punts real,
    puntYards real,
    grossAvgPuntYards real,
    touchbacks real,
    puntsInside20 real,
    longPunt real
);

GRANT INSERT, SELECT ON ALL TABLES IN SCHEMA public TO nfl_backend;