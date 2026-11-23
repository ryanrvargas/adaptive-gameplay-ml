# Adaptive Gameplay and Monetization Using Machine Learning

CSC 475/592 final project. The goal is to predict player behavior from gameplay history, starting with level success, retention and rewarded advertising. In-game purchase prediction is an optional extension.

## Current status

- [x] Project proposal and repository structure
- [ ] Audit the Flood-It! dataset and confirm usable prediction targets
- [ ] Create a tabular dataset and establish baseline models
- [ ] Compare models, tune hyperparameters and benchmark against AutoGluon
- [ ] Document reproducibility and write the final report
- [ ] Optional: build a playable puzzle-game demo
- [ ] Optional: extend to purchase probability and future spending

## Getting started

Python 3.11 is the starting environment. The initial CSV audit uses the standard library. Model dependencies will be pinned after we select the training data and models.

1. Open the [Flood-It! dataset documentation](https://developers.google.com/analytics/bigquery/app-gaming-demo-dataset).
2. Run `sql/event_inventory.sql` in BigQuery after reviewing the source table and estimated query cost. Inspect the counts and available parameters before choosing a target.
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

See [docs/plan.md](docs/plan.md) for the experiment plan and next milestone. Dataset files, trained models, and generated experiment outputs are ignored by Git.

## Structure

| Path | Purpose |
| --- | --- |
| `gameplay_ml/` | Python modules for the audit, future data preparation, training and evaluation |
| `sql/` | Queries used to inspect and later export the public sample |
| `data/` | Local raw and processed data |
| `results/` | Local figures, metrics and models |
| `docs/` | Project plan, dataset decisions and report notes |
| `Dockerfile` | Reproducible starting environment |

The starter audit is functional. Model training, adaptive gameplay and purchase prediction are future milestones.
