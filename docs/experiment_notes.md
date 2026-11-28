# Experiment notes for the research paper

## Research question

Can early gameplay activity predict whether a new Flood-It! player starts another session within the next seven days? Our longer-term goal is to explore adaptive gameplay and rewarded-ad opportunities, but the first experiment is about predicting retention.

## Dataset and experimental design

- Source: Google's public, obfuscated [Flood-It! gameplay dataset](https://developers.google.com/analytics/bigquery/app-gaming-demo-dataset).
- 5,700,000 events, 15,175 unique players, 114 days (2018-06-12 to 2018-10-03), 37 event types.
- Eligible retention cohort: 3,947 distinct players with observed first_open and enough follow-up. One row per player. 1,076 returned (27.26%); 2,871 did not.
- Features: counts of total events, sessions, regular level starts, regular level ends and score submissions in the first 24 hours. The initial features do not include quickplay-specific events, IDs, timestamps, or future activity.
- Target: recorded session_start in the seven days beginning after the initial 24-hour window, binary 0/1.
- Chronological first experiment: 2,795 training players; 790 final test players; 362 excluded at the boundary because their label windows overlap the first test prediction. Five expanding validation folds within training, each with a seven-day gap between the training prediction times and validation prediction times.
- Source ZIP SHA-256: `474e7ed636a5891ace36645fe5d5bc6b593be47b8f3abaef26ef9eee7ed67c79`.

## E01 - Untuned model comparison (T08)

Status: **Code prepared; execution pending.**

Hypothesis: early activity may provide more predictive information than the overall return rate. We will test that by comparing three models against an uninformed dummy classifier. We do not yet know which model will perform best.

| Model | Starting configuration |
| --- | --- |
| Dummy | Prior probability; predicts the more common class at threshold 0.5 |
| Logistic Regression | StandardScaler fitted separately in each training fold, C=1, lbfgs, max_iter=1000 |
| Random Forest | 100 trees; otherwise library defaults |
| XGBoost | 100 trees, max_depth=6, learning_rate=0.3, binary:logistic, hist tree method, logloss evaluation |
 
Random seed 42 for the three trained algorithms; one CPU thread per fit. Python package versions are specified for the starting environment in requirements-baselines.txt; actual Python, operating system, package versions, input hashes, fold assignments by index range, and per-model settings are recorded by the script. We will pin the full environment for the final reproducibility package.

Primary model selection metric: mean average precision (AP) across the five validation folds. AP summarizes the precision-recall curve using recall increments, so it is not interchangeable with trapezoidal PR-AUC. A no-skill ranking has AP equal to validation prevalence. Report mean and sample standard deviation, ROC-AUC, accuracy, balanced accuracy, precision, recall, F1, Brier score and training time. Classification metrics use 0.5 as the probability threshold before tuning. Brier score measures squared probability error (lower is better).

Keep the 790 test players out of all training, preprocessing, model selection and hyperparameter tuning. The first script does not open the test CSV. Synthetic tests are strictly separated from real results.

Results: pending. Fill this table only after verified execution.

| Model | AP mean ± SD | ROC-AUC | Precision | Recall | F1 | Fit time |
| --- | --- | --- | --- | --- | --- | --- |
| Dummy | Pending | Pending | Pending | Pending | Pending | Pending |
| Logistic Regression | Pending | Pending | Pending | Pending | Pending | Pending |
| Random Forest | Pending | Pending | Pending | Pending | Pending | Pending |
| XGBoost | Pending | Pending | Pending | Pending | Pending | Pending |

Run from the project repository with Python:

```sh
python -m pip install -r requirements-baselines.txt
python -m unittest discover -s tests -v
python -m gameplay_ml.prepare_retention path/to/flood_it_audit.zip
python -m gameplay_ml.train_baselines
```

Or download and run [retention_baselines.ipynb](../notebooks/retention_baselines.ipynb) in Colab with the exported ZIP. Output: fold_metrics.csv, model_comparison.csv, experiment.json. The notebook packages just those aggregate files into retention_baseline_results.zip.

## E02 - Hyperparameter search (T09)

Pending. Use the same five chronological folds and same primary metric to select configurations. Record search spaces, sampled configurations, seed, time, best settings and the change from E01. Do not use the test data to choose a threshold or settings.

## E03 - AutoML comparison (T10)

Pending. Compare AutoGluon using the same training feature set, target and time-aware validation. Any validation configuration must avoid random folds that mix future and past labels. Select and freeze methods before evaluating once on the final test set. Record actual hardware, runtime and settings.

## Limitations and interpretation

- The event sample is obfuscated, from 2018, and limited to one game. It is not necessarily representative of current games.
- The cohort includes observed new-player first_open events with enough follow-up; it excludes other players.
- A session_start is a recorded return, not proof that every gameplay visit is logged.
- The inventory contains 1,912 reward events from 354 players, but not a recorded set of offer/decline events or advertising revenue. Reward occurrence is not acceptance probability or money earned.
- The 27 purchase events are too sparse to prioritize a reliable purchase model.
- A predictive model does not establish whether changing difficulty or offering an ad causes higher retention. A controlled experiment would be required.

## HPC plan

E01 is small enough for CPU training. Measure the runtime first, then check UNCW's supported Python modules, SLURM allocation and package setup for larger tuning and AutoML experiments. Record allocated CPUs, memory, elapsed time, software versions, job status and comparisons against local results. Do not assume HPC improves performance until measured.

## Report structure

Use the professor's five-page report format: introduction, dataset description, experimental setup, results (with plots and before/after comparisons), separate code and reproducibility instructions. Keep this file as a detailed record that we can draw from when writing the report.
