# Adaptive Gameplay and Monetization Using Machine Learning

This is my final project for CSC 475/592. I want to see how we can use machine learning to predict how someone will play a game, whether they will come back and if they will watch a rewarded ad. If we have time, I also want to look at predicting in-game purchases.

## Current status

- [x] Project proposal and repository structure
- [x] Go through the Flood-It! dataset and see what we can predict
- [x] Prepare the retention training and testing table
- [ ] Train baseline models
- [ ] Compare models, tune their hyperparameters and compare with AutoGluon
- [ ] Containerize the project and write the final report
- [ ] Optional: build a playable puzzle-game demo
- [ ] Optional: extend to purchase probability and future spending

## Getting started

We are starting with Python 3.11. The first script uses the standard Python library. We will choose and pin the versions of the ML libraries once we know what we are working with.

The easiest way to get the data is to use [the Colab export notebook](notebooks/flood_it_export.ipynb). It runs the four initial SQL queries and gives us a ZIP of the CSVs and query details. See the data audit instructions for the Google Cloud setup.

1. Follow [the data audit instructions](docs/data_audit.md) to get into BigQuery, run the inventory queries and check what we can predict.
2. Once we have the inventory, check the candidate retention table and decide which target to start with.
3. If we export event rows to `data/raw/events.csv` with `user_pseudo_id`, `event_timestamp` and `event_name`, we can run the Python audit from the repository root:

```sh
python -m gameplay_ml.audit data/raw/events.csv
```

Or use Docker:

```sh
docker build -t adaptive-gameplay-ml .
docker run --rm -v "$(pwd)/data:/app/data:ro" adaptive-gameplay-ml data/raw/events.csv
```

To prepare the retention data from the exported ZIP, run:

```sh
python -m gameplay_ml.prepare_retention path/to/flood_it_audit.zip
python -m unittest discover -s tests -v
```

This creates `data/processed/retention_split/` with train/test CSVs and a split summary, including five time-ordered validation folds. Use the five feature columns listed in the summary, not the player IDs or timestamps. The script will not overwrite a previous split; specify a new `--output` directory to repeat it. Keep the final test set untouched during tuning.

Our step-by-step plan is in [docs/plan.md](docs/plan.md). The actual data, trained models and generated results are kept locally and ignored by Git.

## Training the first models

Download [the baseline Colab notebook](notebooks/retention_baselines.ipynb) and run it with the original flood_it_audit.zip. It installs dependencies, runs tests and returns a ZIP of aggregate metrics. This notebook does not access BigQuery.

Or, after preparing the split, run these locally:

```sh
python -m pip install -r requirements-baselines.txt
python -m unittest discover -s tests -v
python -m gameplay_ml.train_baselines
```

Results are written to `results/retention_baselines/`. Real model training is pending; see the experiment notes for the planned method and results status.

## Keeping track of our work

- [TASKS.md](TASKS.md) - What we need to do, by priority, and what's finished or blocked.
- [LOG.md](LOG.md) - What we worked on, problems we ran into and how we handled them.
- [Experiment notes for the paper](docs/experiment_notes.md) - Research question, reproducible method, model settings, metrics, limitations and actual results once available.
- [Using the HPC](docs/hpc.md) - How we plan to use the cluster once we start training and tuning models.

## Structure

| Path | Purpose |
| --- | --- |
| `gameplay_ml/` | Python code for the audit and eventually processing, training and testing the models |
| `sql/` | Queries to look at the data and export it |
| `data/` | Local raw and processed data |
| `results/` | Plots, model results and saved models |
| `docs/` | Project plan, notes on the data and final report |
| `Dockerfile` | Setup to run the code in a container |

The first export has been audited: 5.7 million events from 15,175 players and a candidate retention table of 3,947 players. We will start with seven-day return prediction, then look at gameplay and rewarded ad signals. See the work log for the actual counts and limitations.
