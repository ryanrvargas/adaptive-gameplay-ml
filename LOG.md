# Project work log

This is where we will keep track of what we worked on, what got in the way, how we handled it and what needs to be done next. Keep results from real data separate from test data.

## 2026-11-28 - E02 Windows replication and E03 AutoGluon comparison

- Ryan ran E02 locally: all 360 fits completed, matching the Linux baseline and tuned mean AP values to four decimals. Reported Windows search times: Logistic Regression 2.5 s, RF 46.4 s, XGBoost 15.8 s (64.7 s combined). These are console-reported rounded times, not a verified full duplicate result archive.
- Installed AutoGluon Tabular 1.5.0 in a separate environment because its SciPy constraint conflicts with E01/E02. Added reproducible requirements, training code and tests. Six CPU model families (LR, RF, XT, LightGBM, CatBoost, XGBoost) compete and ensemble on an inner time-ordered holdout with a seven-day purge; no outer validation or test data is used in selection.
- Blocker: refit_full(train_data_extra=...) did not actually include the gap rows in component sample counts. Resolved by explicitly excluding the gap in refit, verifying actual fitted sample counts, repeating the run and documenting the reduced training-size limitation. All five outer AP scores reproduced exactly.
- AutoGluon mean validation AP 0.5524 (SD 0.0567), ROC-AUC 0.7395, accuracy 0.7494, F1 0.3914. It selected a weighted ensemble on each fold. Total fit/refit time 12.68 seconds; no HPC required. Optional PyTorch/CUDA warnings and small-sample quantile warnings were nonfatal.
- Ten tests passed, and all aggregate metrics match the fold records. Archived E03 only as aggregate data. T10 validation finished; final test evaluation still pending. See experiment_notes.md for the full method and comparisons.

## 2026-11-28 - E02 hyperparameter tuning completed (T09)

### What we did

- Added `gameplay_ml/tune_retention.py` with GridSearchCV and two synthetic tests. Used the exact E01 data and five purged folds; 72 configurations and 360 total fits. No final test rows accessed.
- The local execution environment became available. Installed XGBoost and created an isolated Python environment with the same E01 library versions. E02 ran on Linux/Python 3.12.14 rather than Ryan's Windows/Python 3.11.9; all three original configurations reproduced E01 mean AP exactly.
- Archived aggregate metrics and settings in `docs/experiments/E02/`, and documented the search grids, best parameter settings and interpretation in the experiment notes.

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

- The tree models improved substantially, particularly Random Forest. Logistic Regression remains narrowly ahead by AP, but the difference is small relative to fold variation; reserve judgment for the final held-out evaluation.
- Eight unit tests passed. Verified 360 unique fold rows and all candidate summaries/best choices against the recorded scores. Total search wall time: 37.614 seconds. The earlier environment blocker is resolved. No HPC was required for this experiment.

### Next up

T10: AutoGluon comparison on the same features, training rows, chronological validation folds and AP metric. Check compatibility in a separate environment; run the same CPU experiment locally or use the HPC if dependency support or runtime warrants it. Freeze the final comparison settings before opening the held-out test set.

## 2026-11-28 - E01 baseline results from Ryan's laptop (T08)

### What we did

- Ryan ran the baseline experiment on his Windows machine using Python 3.11.9, NumPy 2.2.6, SciPy 1.17.1, scikit-learn 1.7.2, XGBoost 3.0.5, threadpoolctl 3.8.0 and one CPU thread. All 20 model/fold fits returned results. This resolved the previous execution environment blocker.
- Checked the uploaded experiment metadata against our original export hash, verified the training CSV hash against the locally reproduced split, confirmed all five fold sizes and class prevalence, and independently recalculated every mean and sample standard deviation from the 20 fold rows. All matched. The run metadata reports test_used=false.
- Saved the aggregate output files in `docs/experiments/E01/`. No player-level data or credentials were committed.

| Model | Mean AP ± SD | ROC-AUC | Accuracy | Precision | Recall | F1 | Brier | Mean fit (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Logistic Regression | 0.5793 ± 0.0514 | 0.7407 | 0.7579 | 0.6902 | 0.2866 | 0.4044 | 0.1720 | 0.0038 |
| XGBoost | 0.4921 ± 0.0433 | 0.6823 | 0.7219 | 0.5210 | 0.4082 | 0.4568 | 0.2057 | 0.0665 |
| Random Forest | 0.4664 ± 0.0394 | 0.6861 | 0.7082 | 0.4898 | 0.4299 | 0.4565 | 0.2017 | 0.1614 |
| Dummy | 0.2884 ± 0.0413 | 0.5000 | 0.7116 | 0.0000 | 0.0000 | 0.0000 | 0.2058 | 0.0003 |

### What we learned

- Logistic Regression ranked first by the prespecified primary metric, average precision, in all five validation folds. It improved AP by 0.2909 absolute over the dummy model (about twice the baseline AP) and by 0.0872 over untuned XGBoost. It also had highest mean ROC-AUC and lowest Brier score.
- At threshold 0.5, Logistic Regression has high precision but low recall. It misses about 71% of recorded returners in the validation folds. XGBoost and Random Forest achieved higher F1 and recall at the same threshold, despite worse ranking performance. A threshold can be selected using training validation predictions later if justified by the use case; do not tune it on the held-out test set.
- Performance varies across folds; these are validation statistics, not final test results. The 790 test players remain reserved.
- Total measured fit time for the 20 fits was 1.160 seconds (not total end-to-end runtime). This is evidence that this small cohort does not require HPC for baseline fits. We will time the hyperparameter search and consider HPC for larger searches or AutoGluon rather than assuming it is faster.

### Next up

T09: run hyperparameter search with the same folds, primary AP metric and fixed seed. Compare untuned and tuned configurations; retain the final test set for the end of model selection.

## 2026-11-27 - Baseline experiment code and paper notes (T08)

### What we did

- Added `gameplay_ml/train_baselines.py` and fixed starting configurations for DummyClassifier, Logistic Regression, Random Forest and XGBoost. Logistic Regression scales features inside each fold. The two tree models do not require scaling.
- Reuse all five chronological validation folds and the exact five initial gameplay features. The script never opens the final test CSV.
- Select using mean average precision (AP); record mean and standard deviation for AP, ROC-AUC, accuracy, balanced accuracy, precision, recall, F1, Brier score and fit time. Use probability threshold 0.5 and seed 42. Record package versions, platform, hashes, configuration and fold indices in experiment.json.
- Added two synthetic experiment tests and requirements-baselines.txt. Added a standalone Colab notebook to reproduce the split, run all tests, train the four baselines and download only aggregate results.
- Created `docs/experiment_notes.md` for the paper: research question, verified dataset counts, feature and label definitions, split protocol, experiment settings, evaluation metrics, hypotheses, limitations and future tuning/AutoGluon/HPC comparisons.

### Blocker and workaround

- The current Python execution environment is unavailable, so we could not run the new tests or execute E01 on real data. No training metrics or runtime have been measured. Do not record estimated or synthetic scores as real results.
- Run the self-contained `notebooks/retention_baselines.ipynb` in Colab with the existing Flood-It ZIP. No BigQuery calls or Google Cloud credentials are needed. Alternatively run the Python scripts on a local CPU. No new cloud resources or HPC jobs were submitted.

### Next up

Run E01, verify the result ZIP and add the actual fold-level and mean validation results to the experiment notes. Compare the models before beginning T09 hyperparameter selection.

## 2026-11-27 - Prepare the retention training and testing sets (T07)

### What we did

- Added `gameplay_ml/prepare_retention.py` to load the Colab ZIP, check required fields and split players chronologically. It writes ignored local train/test CSVs and a summary with the five validation folds.
- Features: first 24 hours of total events, sessions, level starts, level ends and scores posted. The target is whether a session starts in the next seven days. IDs and timestamps are only for checking and splitting, not model inputs.
- The last approximately 20% of players are the final test set. Players with a common prediction timestamp stay together. Remove training rows whose seven-day label windows extend past the earliest test prediction.

| Split | Players | Returned | Did not return |
| --- | ---: | ---: | ---: |
| Training | 2,795 | 818 | 1,977 |
| Gap (excluded) | 362 | 81 | 281 |
| Test | 790 | 177 | 613 |

- First test prediction: September 9, 2018, at 01:44:20.385 UTC. All training labels end by that time.
- Five expanding-window validation folds on training data only, using the same seven-day gap before each validation block. Each validation fold contains 466 players; training sizes are 357, 663, 1,146, 1,448 and 2,073. Both classes appear in all training and validation folds.
- The 72.7% overall non-return rate is why accuracy alone is not enough. Compare PR-AUC, recall, precision and F1 with a dummy baseline; reserve held-out testing until model selection and tuning are done.

### Verification

- Four unit tests passed for timestamp ties, time gaps, five folds, sorting/label conversion, duplicate IDs and invalid feature windows.
- Verified all 3,947 player IDs accounted for without overlap, all split/fold training label windows end before or at the next evaluation prediction, and identical outputs on rerun.
- No new packages, HPC jobs or database queries required. No model trained yet. Raw player rows and generated split files are not committed.

### Next up

T08: train and compare baseline models using the validation folds. Run `python -m gameplay_ml.prepare_retention path/to/flood_it_audit.zip` from the repository root to reproduce these splits.

## 2026-11-27 - Flood-It! data obtained and audited

### What we did

- Ryan ran the notebook and uploaded `flood_it_audit.zip`. This resolves the Google authorization blocker for the initial export.
- Checked ZIP integrity, all four CSV row counts against the manifest, and the event inventory total against the dataset summary. All checks passed. The manifest records 1.823 GiB estimated and 1.825 GiB billed, below the 25 GiB cap. Billed bytes are usage, not a statement of dollars charged.
- Source: 5,700,000 events, 15,175 unique players, 114 days from June 12 through October 3, 2018. There are 37 event types and 205 event/parameter pairs. No missing player IDs, timestamps or event names in the summary.
- Candidate training table: 3,947 unique players (91.4% of the 4,319 players with a recorded first_open), 1,076 returned in the next seven days (27.26%) and 2,871 did not (72.74%). All required fields are present, no duplicate players, all feature windows are 24 hours, all feature counts are nonnegative and event-specific counts do not exceed total early events. The earliest and latest first-open timestamps are June 12 and September 26, 2018 UTC.
- The export contains 1,912 ad_reward events across 354 players. It has ad unit, type, reward value and some ad event IDs, but the inventory does not show ad offers, declines or ad revenue. We can investigate prediction of future recorded rewards, not acceptance probability or cash revenue.
- Quickplay has 523,430 starts, 191,088 completions, 137,035 failures and 122,278 resets. The board parameter is present on starts, completions and failures. These support exploring a level-success model, but we need to establish reliable attempt/outcome matching first. Only 27 in-app purchase events from 27 players were recorded, so we will not prioritize a purchase model.
- Selected seven-day return as the first model target. The first five features use the first 24 hours, and the label uses only subsequent activity. A majority-class baseline is necessary because about 73% of this cohort did not return.

### Next up

- Finalize chronological splitting and use time-aware validation. A candidate 80/20 chronological split gives 790 test players; requiring training label windows to end by the first test prediction retains 2,795 training players and excludes 362 near the boundary. Confirm tie handling and split implementation before training.
- Compare the dummy baseline, Logistic Regression, Random Forest and XGBoost. After establishing baseline performance, consider adding quickplay and reward features and a separate future ad-reward target. Keep raw IDs and player-level CSVs out of Git.
- No models have been trained yet. No HPC is needed for the initial table of 3,947 rows.

Export SHA-256: `474e7ed636a5891ace36645fe5d5bc6b593be47b8f3abaef26ef9eee7ed67c79`.

## 2026-11-26 - Colab account access and runtime authorization

- Successfully signed in to Colab and opened the export notebook. Started a Python runtime.
- Reviewed the code and Google's documentation before authorizing the notebook. It queries only the public Flood-It dataset, uses dry runs and a 25 GiB scan cap, and does not read private Drive files or change cloud settings.
- The additional Google credential authorization failed at the account verification step with a sign-in error. No live BigQuery query results were obtained.
- Next: complete notebook authorization through a trusted browser or run the same notebook locally in the user's signed-in Colab session, then provide the exported ZIP for the dataset audit.

## 2026-11-26 - Colab sign-in follow-up

- Tried opening BigQuery again. The console returned Site Unavailable. Colab opens, but the shared browser is still signed out after the sign-in attempt expired.
- Uploaded the verified export notebook to Google Drive so it is ready to open from an authenticated Colab session. The notebook contains the four SQL queries and the same 25 GiB cap.
- Still blocked on live BigQuery access and getting the ZIP with real data. No actual queries ran and no model training started.

## 2026-11-26 - Getting access to the data

### What we did

- Confirmed that Google offers free BigQuery sandbox projects without a credit card or paid billing. Google documents a free allowance of 1 TiB of query processing each month.
- Made `notebooks/flood_it_export.ipynb` so we can get the data in Colab with a Google sign-in and project ID. The notebook estimates query sizes first, applies a 25 GiB per-run cap and exports the initial results into one ZIP. It uses the same four SQL queries we already wrote.
- Updated the README, task list and data audit instructions with the steps to get the data.

### Blockers and how we handled them

- We still need an authenticated BigQuery-enabled project to run the actual queries. The Colab workflow allows Ryan to authenticate on his own account and send us the exported data. We do not need to exchange credentials or set up paid services.

### Verification

- All notebook code cells compiled and the four embedded queries matched the SQL files in the repo.
- Tested the notebook export with mock query results. It wrote four CSVs and a manifest into a ZIP successfully. Live BigQuery authentication and query execution are still unverified.

### Next up

Run the notebook with a sandbox project. Get `flood_it_audit.zip`, review the actual events and candidate retention rows, and decide which model we should start with.

## 2026-11-23 - Project setup and data audit

### What we did

- Created the private GitHub repository with the proposal plan, basic Python audit script, Dockerfile and folders for the data and results.
- Reviewed the project instructions and kept the main goal focused on adaptive gameplay, retention and rewarded ads. Purchase prediction is something we can add if we have time.
- Checked Google's Flood-It! dataset documentation and confirmed it is an obfuscated sample covering 114 days. The actual table still needs to be queried.
- Added a prioritized task list, this log, more detailed dataset inventory queries and instructions for exporting the first candidate retention table.
- Decided to use the first 24 hours of observed new-player activity as a possible feature window and the following seven days as a possible label window. We will review the real sample counts before choosing the final target.

### Blockers and how we handled them

- BigQuery requires a Google Cloud project with the BigQuery API enabled. The current coding environment has no `bq` or `gcloud` CLI. We also tried opening the BigQuery console, but it showed "Site Unavailable" on both attempts. We prepared the queries and documented how to run them. We still need access to a project (the free sandbox is an option) and actual query results. No paid resources were created.
- The public sample is obfuscated. We need to check event names, parameters and the dates before assuming it has ad offers, level outcomes or revenue amounts. We added SQL to check the available parameters and count candidate retention rows.
- The Docker runtime is not installed in the current coding environment. We can test the Python audit directly for now, and verify the container later on a machine with Docker or a compatible HPC container runtime.

### Verification

- The starter CSV audit ran on a small synthetic example. It counted three events from two players and caught a missing timestamp. It also correctly rejected a CSV missing a required column. These are test results, not gameplay findings.
- The retention table audit accepted a two-player synthetic CSV with one returning player and one who did not return. It rejected a second example with a duplicate player, an invalid time window and a negative count.
- Tested the retention query logic with synthetic events in SQLite, using a stand-in for BigQuery's `COUNTIF`. It correctly excluded incomplete follow-up, kept future events out of the input features and handled both time-window boundaries. The actual SQL queries still need a live BigQuery run for verification.
- Python compilation and `git diff --check` passed.

### Next up

T03: access BigQuery. T04: collect the inventory results. Then check the candidate retention cohort, and decide whether retention or another target has enough usable data for our first model.
