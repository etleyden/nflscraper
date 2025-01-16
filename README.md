# NFL Game Outcome Predictor

This repository is my attempt at trying to predict the outcome of an NFL game based on known factors. 

Here are the best results so far (just a hair above random guessing):

```
Decision Tree F1: 0.5042 +/- 0.0459
Decision Tree Acc: 0.5379 +/- 0.0469
SVM F1: 0.5472 +/- 0.0205
SVM Acc: 0.5976 +/- 0.0156
Neural Network F1: 0.3373 +/- 0.1468
Neural Network Acc: 0.5710 +/- 0.0405
```

Observations:
- Beginning to see decreasing returns on increasing data, with the biggest gains on increase in data being with a NN still (adding 2016 and 2015 seasons increased F1 by ~0.2)
- NN is still incredibly low, suggesting more data could improve this metric
- SVM is the best by far, with default parameters. Grid search currently in progress.

## Getting Started

The `data` folder has everything you need:

* Set up a Postgres database, and create the relations using `nfl_create.sql`. Put the credentials in a `.env`.
* Use `build_db.py [YYYY]` to collect data from various APIs, namely the [ESPN API](https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates=2023), and [nflweather.com](https://www.nflweather.com/) (huge thanks to the developers of these services).
    * Example Usage: `python build_db.py 2023` (accrues all data for NFL games that occurred in 2023 and writes the data to the DB)
* Use `generate_csv.py` to generate a ML friendly CSV with aggregated game data, with labels of "Home" and "Away" depending on who won the game.
* Finally, `train_model.py` will train three different models using 5-fold cross-validation (if there's more or less, its because I forgot to change this README) and output their results. At the time of writing, we have a decision tree, SVM, and neural network with default parameters. 

## Contributing

Here are some easy TODOs for anyone interested in contributing to the project:

- documentation for `generate_csv.py`, since the configuration options for the CSV are almost infinite.
- fine-tuning parameters in train_model.py, and potentially adding more suitable models.
- the project is set up as if we're utilizing cuda cores, but it doesn't actually use them
- update build_db.py to collect game data for prior seasons to 2015 (2023-2015 ~= 2656 samples). As of right now, it'll probably *mostly* work, but there's anomalies in some seasons that don't occur in others that result in imperfect data. I've only optimized up to 2017.
- The `dataviewer` directory is supposed to be a semi-separate project focused on being able to comprehensively review the data that we collected, maybe make updates to individual lines if necessary -- but mostly just provide visualization options for the data so we can discover some potentially useful insights. 
- email me at etleyden@gmail.com with some cool research papers on this topic