# Project plan

## Primary scope

Use historical gameplay to predict level success, future rewarded ad usage and player retention. Focus on a single reliable target first so the core machine learning assignment can be completed. An original puzzle-game demo may illustrate predictions after model evaluation.

## Milestone 1: dataset audit

Source: [Google's Flood-It! BigQuery sample dataset](https://developers.google.com/analytics/bigquery/app-gaming-demo-dataset). The sample is obfuscated and spans 114 days. Confirm the data rather than assuming event definitions or valid monetary fields.

- Inspect event names, counts, date coverage, distinct players and missing fields.
- Inspect parameters associated with session, level, score, reward and ad events.
- Determine whether attempts and outcomes can be matched reliably.
- Determine whether ad offers and their outcomes are recorded. If offers are absent, predict future reward-event occurrence or count instead of acceptance probability.
- Confirm event timing and sufficient follow-up for a seven-day retention label.
- Document the chosen target, feature cutoff, observation window and label window.

Completion criteria: a documented audit with a usable target, feature list and eligible sample count.

## Milestone 2: tabular data and model selection

Build a table with one row per eligible player or attempt. Use only information from before the prediction cutoff. Preserve timestamps and player IDs for splitting, without using raw player IDs as predictors.

Reserve approximately 20% as an untouched test set. Use five-fold cross-validation on training data, respecting player grouping or chronology as appropriate. Compare a simple baseline with Logistic Regression, Random Forest and XGBoost for classification, or regression variants for numeric outcomes.

## Milestone 3: tuning and evaluation

Use grid search or randomized search, record the search ranges and best parameters, and benchmark against AutoGluon with the same data and metric. Compare default and tuned performance. Use precision, recall, F1 and precision-recall AUC for classification and MAE for regression as appropriate to the selected task. Include plots and reproducibility instructions. Ensembling is optional.

## Milestone 4: optional demonstration

Build a small original puzzle-game prototype that illustrates model predictions and optional rewards. Historical outcome prediction alone cannot establish the effect of changing difficulty or ad placement. Any effectiveness claim requires a controlled experiment.

## Milestone 5: optional purchase prediction

Check for enough purchase events and reliable amounts. If suitable, predict future purchase probability and future spending. Compare behavior-only features with early purchase history and estimate combined revenue only when both ad and purchase monetary values are available.

## Class submission

Submit code and a reproducible workflow with a report of at most five pages. Include the problem, dataset description, experimental setup, before/after tuning results, best configuration, plots and AutoML comparison. Zip the files for Canvas.
