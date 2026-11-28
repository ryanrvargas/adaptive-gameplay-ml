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

Status: **Completed and verified on Ryan's Windows laptop (2026-11-28).**

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

Results: five-fold chronological validation, not final test performance. The aggregate output files are archived in [E01](experiments/E01/).

| Model | Mean AP ± SD | ROC-AUC | Accuracy | Precision | Recall | F1 | Brier | Mean fit (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Logistic Regression | 0.5793 ± 0.0514 | 0.7407 | 0.7579 | 0.6902 | 0.2866 | 0.4044 | 0.1720 | 0.0038 |
| XGBoost | 0.4921 ± 0.0433 | 0.6823 | 0.7219 | 0.5210 | 0.4082 | 0.4568 | 0.2057 | 0.0665 |
| Random Forest | 0.4664 ± 0.0394 | 0.6861 | 0.7082 | 0.4898 | 0.4299 | 0.4565 | 0.2017 | 0.1614 |
| Dummy | 0.2884 ± 0.0413 | 0.5000 | 0.7116 | 0.0000 | 0.0000 | 0.0000 | 0.2058 | 0.0003 |

The source ZIP and train CSV hashes match our verified split; all 20 fold rows, fold sizes, return rates, means and sample standard deviations check out. Environment: Python 3.11.9, NumPy 2.2.6, SciPy 1.17.1, scikit-learn 1.7.2, XGBoost 3.0.5, threadpoolctl 3.8.0, Windows, one CPU thread per fit. Total model fit time was 1.160 seconds, excluding data loading and evaluation.

Interpretation: Logistic Regression ranked first by AP in all five folds, improved AP by 0.2909 absolute over the dummy and had the lowest Brier score. XGBoost and Random Forest had better F1 at threshold 0.5; Logistic Regression only detected 28.7% of actual returners at that threshold. This motivates tuning and, if useful, selecting a different threshold using validation data. These experiments show predictive association, not a causal effect of changing gameplay. We have not used the final test set.

Run from the project repository with Python:

```sh
python -m pip install -r requirements-baselines.txt
python -m unittest discover -s tests -v
python -m gameplay_ml.prepare_retention path/to/flood_it_audit.zip
python -m gameplay_ml.train_baselines
```

Or download and run [retention_baselines.ipynb](../notebooks/retention_baselines.ipynb) in Colab with the exported ZIP. Output: fold_metrics.csv, model_comparison.csv, experiment.json. The notebook packages just those aggregate files into retention_baseline_results.zip.

## E02 - Hyperparameter search (T09)

Status: **Completed and verified (2026-11-28).**

Used scikit-learn GridSearchCV with the same five expanding, seven-day-purged folds and the original E01 estimators. All 72 configurations were evaluated (360 total fits), including each untuned baseline. Scored using the same average precision, ROC-AUC, accuracy, balanced accuracy, precision, recall, F1 and Brier score functions as E01, with threshold 0.5. Picked the highest mean validation AP per model, first candidate in deterministic grid order for exact ties. Refit disabled; the held-out test set was never loaded. The selected validation scores may be optimistic due to searching the same folds.

| Model | Grid | Configurations |
| --- | --- | ---: |
| Logistic Regression | C = 0.001, 0.01, 0.1, 1, 10, 100; class_weight = None, balanced | 12 |
| Random Forest | n_estimators = 100, 200; max_depth = None, 3, 6, 10; min_samples_leaf = 1, 5, 15 | 24 |
| XGBoost | n_estimators = 100, 200; max_depth = 2, 3, 6; learning_rate = 0.03, 0.1, 0.3; min_child_weight = 1, 5 | 36 |

| Model | E01 AP | E02 AP ± SD | AP change | ROC-AUC | Accuracy | Precision | Recall | F1 | Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Logistic Regression | 0.5793 | 0.5814 ± 0.0552 | +0.0021 | 0.7427 | 0.7579 | 0.6940 | 0.2835 | 0.4017 | 0.1719 |
| Random Forest | 0.4664 | 0.5769 ± 0.0584 | +0.1105 | 0.7556 | 0.7622 | 0.6354 | 0.3976 | 0.4890 | 0.1680 |
| XGBoost | 0.4921 | 0.5715 ± 0.0504 | +0.0794 | 0.7475 | 0.7648 | 0.6539 | 0.3741 | 0.4756 | 0.1689 |

| Model | Selected parameters | Search wall time (s) |
| --- | --- | ---: |
| Logistic Regression | C=0.1, class_weight=None | 0.644 |
| Random Forest | 100 trees, max_depth=3, min_samples_leaf=1 | 31.014 |
| XGBoost | 100 trees, max_depth=2, learning_rate=0.03, min_child_weight=1 | 5.956 |

E01 was run on Ryan's Windows laptop (Python 3.11.9). E02 ran on Linux (Python 3.12.14) after creating an isolated environment with the same recorded NumPy, SciPy, scikit-learn, XGBoost and threadpoolctl versions. All three original hyperparameter configurations reproduced the E01 mean AP scores exactly. Total search wall time was 37.614 seconds, not directly comparable with E01 fit-only timing. No HPC job needed for this search.

Logistic Regression remains first by AP, but the gap to Random Forest is only 0.0044; the fold variation is much larger, so we should not claim a clear winner. Restricting tree depth improved both tree models substantially, consistent with reduced overfitting, though that mechanism is not proven by validation scores alone. Random Forest has the best tuned F1, ROC-AUC and Brier score at the fixed threshold; XGBoost has the highest accuracy. Continue to select by AP, which was set before training. Test performance is unknown.

All 8 unit tests passed (including synthetic tests for the baseline and tuning). Independently checked 360 unique candidate/fold rows, 72 means and sample SDs for every metric, best AP selection, source/training hashes, folds and the original E01 scores. The aggregate output is archived in [E02](experiments/E02/). No player-level data committed.

To reproduce from the original repo and prepared split:

```sh
python -m gameplay_ml.tune_retention
```

Outputs: candidate_metrics.csv, fold_metrics.csv, tuned_comparison.csv and experiment.json in results/retention_tuning/. Existing results are not overwritten; use --output with a new folder to rerun.


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
