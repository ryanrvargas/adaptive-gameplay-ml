# Adaptive Gameplay and Monetization Using Machine Learning

This is my final project for CSC 475/592. I want to see how we can use machine learning to predict how someone will play a game, whether they will come back and if they will watch a rewarded ad. If we have time, I also want to look at predicting in-game purchases.

## Current status

- [x] Project proposal and repository structure
- [ ] Go through the Flood-It! dataset and see what we can predict
- [ ] Put the data into a table and train baseline models
- [ ] Compare models, tune their hyperparameters and compare with AutoGluon
- [ ] Containerize the project and write the final report
- [ ] Optional: build a playable puzzle-game demo
- [ ] Optional: extend to purchase probability and future spending

## Getting started

We are starting with Python 3.11. The first script uses the standard Python library. We will choose and pin the versions of the ML libraries once we know what we are working with.

1. Open the [Flood-It! dataset documentation](https://developers.google.com/analytics/bigquery/app-gaming-demo-dataset).
2. Check the source table and estimated query cost in BigQuery, then run `sql/event_inventory.sql`. See how many events and players we have and check the available event parameters before deciding what to predict.
3. Export selected event rows to `data/raw/events.csv` with `user_pseudo_id`, `event_timestamp`, and `event_name` columns.
4. Run the starter audit from the repository root:

```sh
python -m gameplay_ml.audit data/raw/events.csv
```

Or use Docker:

```sh
docker build -t adaptive-gameplay-ml .
docker run --rm -v "$(pwd)/data:/app/data:ro" adaptive-gameplay-ml data/raw/events.csv
```

Our step-by-step plan is in [docs/plan.md](docs/plan.md). The actual data, trained models and generated results are kept locally and ignored by Git.

## Structure

| Path | Purpose |
| --- | --- |
| `gameplay_ml/` | Python code for the audit and eventually processing, training and testing the models |
| `sql/` | Queries to look at the data and export it |
| `data/` | Local raw and processed data |
| `results/` | Plots, model results and saved models |
| `docs/` | Project plan, notes on the data and final report |
| `Dockerfile` | Setup to run the code in a container |

For now the audit script works with an exported CSV. Once we look at the actual dataset, we can start training our models.
