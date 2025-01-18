# NFL Prediction Model

This repository is my attempt at trying to predict the outcome of an NFL game based on known factors. 

Here are the best results so far (just a hair above random guessing):

```
Decision Tree F1: 0.4976 +/- 0.0305
Decision Tree Acc: 0.5299 +/- 0.0258
SVM F1: 0.4910 +/- 0.0293
SVM Acc: 0.5719 +/- 0.0211
Neural Network F1: 0.4821 +/- 0.0992
Neural Network Acc: 0.5854 +/- 0.0303
```

Observations:
- Seeing reduced returns on increasing data, indicating an issue with data prior to 2017 either on my end or on its usefulness in general.
- NN is still incredibly low, suggesting more data could improve this metric
- SVM is the best by far, with default parameters. Grid search currently in progress.

## Getting Started

The `src` folder has everything you need:

* Set up a Postgres database, and create the relations using `nfl_create.sql`. Put the credentials in a `.env`.
* Use `build_db.py [YYYY]` to collect data from various APIs, namely the [ESPN API](https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?limit=1000&dates=2023), and [nflweather.com](https://www.nflweather.com/) (huge thanks to the developers of these services).
    * Example Usage: `python build_db.py 2023` (accrues all data for NFL games that occurred in 2023 and writes the data to the DB)
* Use `generate_csv.py` to generate a ML friendly CSV with aggregated game data, with labels of "Home" and "Away" depending on who won the game.
* Finally, `train_model.py` will train three different models using 5-fold cross-validation (if there's more or less, its because I forgot to change this README) and output their results. At the time of writing, we have a decision tree, SVM, and neural network with default parameters. 

`data/` directory contains pre-compiled CSV from my local database so you can jump right into model training without doing a bunch of collection yourself.

## Contributing

Here are some easy TODOs for anyone interested in contributing to the project:

- documentation for `generate_csv.py`, since the configuration options for the CSV are almost infinite.
- fine-tuning parameters in train_model.py, and potentially adding more suitable models. (grid searches for SVM and NN)
- update build_db.py to collect game data for prior seasons to 2015 (2023-2015 ~= 2656 samples). As of right now, it'll probably *mostly* work, but there's anomalies in some seasons that don't occur in others that result in imperfect data. I've only optimized up to 2017.
    - Note that increasing the volume of data is expected to improve results, however at this time, improving the quality of the data in preprocessing is probably more effective.
- The `src/dataviewer` directory is supposed to be a semi-separate project focused on being able to comprehensively review the data that we collected, maybe make updates to individual lines if necessary -- but mostly just provide visualization options for the data so we can discover some potentially useful insights. 
- email me at etleyden@gmail.com with some cool research papers on this topic