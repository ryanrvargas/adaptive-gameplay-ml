# Project work log

This is where we keep track of what we did, what got in the way, how we fixed it and what we need to work on next. Keep the real results separate from our practice runs.

## 2026-11-28 - BigQuery access issue (T11a.2)

- I tried running the extended export in Colab. The first dry run returned a 403 Forbidden error because the signed-in account does not have `bigquery.jobs.create` on the selected Google Cloud project. Neither query ran, and we have no new data from this attempt.
- Checked Google's BigQuery documentation. We need to confirm we are using the same Google account and sandbox project that worked for the first export. If the account is correct, the project administrator needs to grant the BigQuery Job User role. No changes to the SQL, billing or permissions were made.
- Next: fix the account/project access, rerun the dry-run cell and only continue with the export if the scan is within the cap. Keep the completed retention experiments unchanged.

## 2026-11-28 - Getting more gameplay data (T11a)

### What we did

- We went back through the event inventory and checked what information we have for quickplay and ad rewards. There are 523,430 recorded quickplay starts and 1,912 recorded ad rewards from 354 players. We still need the player-level labels before we know if we have enough data for either model.
- Made two SQL files and a new Colab notebook. The first table uses the first 24 hours to predict whether a player earns an ad reward in the next seven days. The second tries to match each quickplay start with a win or loss on the same board within one hour. We leave unclear matches blank instead of assuming they lost.
- Added an audit script that checks the labels, counts and time windows and tells us how many positive and negative examples we would have after a chronological split. It also checks how many players appear in both parts of the quickplay split.
- Both SQL files passed a BigQuery-dialect syntax check. The notebook code compiled and contained the same two queries as the SQL files. All three new synthetic audit tests passed. These checks are not a live BigQuery run, so we still have to check the dry run and actual export.

### What got in the way

- The data we already exported doesn't have the detailed events we need for these two models. The new notebook is ready, but we still need to run it through our existing BigQuery project. No billing or new project needed.
- We can predict whether someone earns a recorded reward, not whether they accept an ad or how much money they generate. We also can't assume a missing outcome means a loss.

### Next up

Run `notebooks/flood_it_extended_export.ipynb` in Colab, check the scan estimate and download `flood_it_extended.zip`. Once we have it, we'll run the audit and decide which model has enough data to train. Keep the retention results as they are.

## 2026-11-28 - T11 paper figures completed

- Added `gameplay_ml/plot_results.py`, `requirements-plots.txt` and a figure-generation test.
- Used only archived aggregate E01–E04 metrics. Validated E01/E02 baseline AP consistency and the 790-player confusion-matrix totals. No new model fits or test-driven changes.
- Generated three SVG and 300 DPI PNG figures: before/after tuning (mean AP and sample SD), validation versus held-out AP (including the different dummy prevalences), and four final confusion matrices at threshold 0.5. Reviewed each PNG visually; archived SVGs and proposed captions in `docs/figures/`. The plotting test passed.
- What we learned: tuning helped Random Forest the most. The models ranked differently on the test set, and the confusion matrices show how many players who actually returned were missed. The validation-selected Logistic Regression correctly identified 54 of 177 returners; tuned XGBoost identified 71. Accuracy alone overstates usefulness because 613 of 790 test players did not return. Error bars represent descriptive fold SD, not confidence intervals.
- No blocker or HPC required. T11 complete; next is the enriched gameplay/reward-data feasibility check (T11a). It must be a separate exploratory analysis with a prespecified evaluation protocol; do not use the E04 test results to choose configurations.

## 2026-11-28 - Windows AutoML replication and E04 final test evaluation

- I ran AutoGluon again on my Windows laptop after we fixed the typing_extensions issue. All five outer folds finished. Console AP values: 0.4869, 0.6358, 0.5423, 0.5812, 0.5008; mean 0.5494. Low available memory (184–455 MB reported) caused LightGBM to skip in all five folds via its memory-early-stop callback ('NoneType' object is not iterable); XGBoost emitted memory warnings. Do not count this as an exact six-model replication. Use the verified Linux E03 result for the formal comparison. No need to disable memory guards or install PyTorch.
- Before we looked at the test results, we saved the E04 protocol in GitHub. It includes the tuned Logistic Regression we chose during validation, the other baseline/tuned models, the 0.5 threshold, the AutoGluon models and the package versions. Added evaluate_retention.py. Verified original export hash, train hash, chronological split contents and disjoint time windows. Both environments evaluated the same 790 players (177 positive, 613 negative).
- Manual environment initially lacked XGBoost after environment restart; installed the exact 3.0.5 dependency in that environment before manual training. AutoGluon successfully trained all six model families in clean Linux; refitted component models used 2,529 rows (1,970 inner fit + 559 tuning; 266 inner-gap rows excluded). Manual models used all 2,795 training rows.
- Saved both sets of results and the protocol under docs/experiments/E04/. We checked the file hashes and used the confusion matrices to verify accuracy, precision and recall. Individual predictions and player IDs were left out of GitHub.

| Model | Test AP | ROC-AUC | Accuracy | Precision | Recall | F1 | Brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Dummy | 0.2241 | 0.5000 | 0.7759 | 0.0000 | 0.0000 | 0.0000 | 0.1786 |
| Logistic Regression (untuned) | 0.4510 | 0.7128 | 0.7962 | 0.5851 | 0.3107 | 0.4059 | 0.1581 |
| Logistic Regression (tuned; validation-selected) | 0.4536 | 0.7133 | 0.7975 | 0.5934 | 0.3051 | 0.4030 | 0.1577 |
| Random Forest (untuned) | 0.3818 | 0.6844 | 0.7532 | 0.4477 | 0.4350 | 0.4413 | 0.1782 |
| Random Forest (tuned) | 0.4704 | 0.7368 | 0.7848 | 0.5280 | 0.3729 | 0.4371 | 0.1534 |
| XGBoost (untuned) | 0.4322 | 0.6909 | 0.7608 | 0.4577 | 0.3672 | 0.4075 | 0.1743 |
| XGBoost (tuned) | 0.4671 | 0.7398 | 0.7899 | 0.5420 | 0.4011 | 0.4610 | 0.1530 |
| AutoGluon | 0.4763 | 0.7378 | 0.7899 | 0.5455 | 0.3729 | 0.4430 | 0.1535 |

- AutoGluon had highest observed test AP, while tuned XGBoost led ROC-AUC and F1 and tuned Logistic Regression led accuracy. The validation-selected model remains tuned Logistic Regression; we do not choose a new winner or tune settings using test data. Differences between models are small on this single later cohort. Test AP was lower than validation AP; lower test return prevalence (22.4% vs 28.8% mean validation) and temporal differences are plausible factors, not proven explanations.
- All tuned classifiers improved test AP compared with their untuned versions. No HPC needed for these CPU experiments. Next: T11 plot results and explain the model comparison, then reproducibility/containerization and report; optional new targets must use a new prespecified evaluation rather than tuning this test set.

## 2026-11-28 - Fix AutoGluon clean-install error on Windows

- The AutoML packages installed on my laptop, but trying to import AutoGluon gave us ModuleNotFoundError: No module named 'typing_extensions'. The earlier Linux environment inherited typing_extensions from the system Python, masking the missing dependency. The error occurred before model training; it does not change E03 results.
- Added typing_extensions==4.16.0 to requirements-automl.txt. Tested a fresh Linux virtual environment without system site packages, installed the corrected requirements, ran pip check (no broken requirements), and reran all five real validation folds. Every AP score matched the archived E03 results exactly; mean AP remained 0.5524.
- Ryan can repair the existing Windows virtual environment with the updated requirements (no need to recreate it) and rerun train_automl. Windows-specific verification is pending. Do not install PyTorch just to suppress optional GPU detection warnings; this experiment is CPU-only.

## 2026-11-28 - E02 Windows replication and E03 AutoGluon comparison

- I ran E02 on my laptop. All 360 fits finished, and the baseline and tuned mean AP scores matched our Linux run to four decimals. Reported Windows search times: Logistic Regression 2.5 s, RF 46.4 s, XGBoost 15.8 s (64.7 s combined). These are console-reported rounded times, not a verified full duplicate result archive.
- Installed AutoGluon Tabular 1.5.0 in a separate environment because its SciPy constraint conflicts with E01/E02. Added reproducible requirements, training code and tests. Six CPU model families (LR, RF, XT, LightGBM, CatBoost, XGBoost) compete and ensemble on an inner time-ordered holdout with a seven-day purge; no outer validation or test data is used in selection.
- Issue: refit_full(train_data_extra=...) wasn't using the extra gap rows like we expected. We removed that argument, checked the number of rows each model actually trained on and ran it again. AutoGluon used fewer training rows as a result. All five outer AP scores reproduced exactly.
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

- The tree models got a lot better, especially Random Forest. Logistic Regression was still slightly ahead in AP, but the scores were too close to call a clear winner before testing.
- Eight unit tests passed. Verified 360 unique fold rows and all candidate summaries/best choices against the recorded scores. Total search wall time: 37.614 seconds. The earlier environment blocker is resolved. No HPC was required for this experiment.

### Next up

T10: AutoGluon comparison on the same features, training rows, chronological validation folds and AP metric. Check compatibility in a separate environment; run the same CPU experiment locally or use the HPC if dependency support or runtime warrants it. Freeze the final comparison settings before opening the held-out test set.

## 2026-11-28 - E01 baseline results from Ryan's laptop (T08)

### What we did

- I ran the baseline experiment on my Windows laptop using Python 3.11.9, NumPy 2.2.6, SciPy 1.17.1, scikit-learn 1.7.2, XGBoost 3.0.5, threadpoolctl 3.8.0 and one CPU thread. All 20 model/fold fits returned results. This resolved the previous execution environment blocker.
- Checked the uploaded experiment metadata against our original export hash, verified the training CSV hash against the locally reproduced split, confirmed all five fold sizes and class prevalence, and independently recalculated every mean and sample standard deviation from the 20 fold rows. All matched. The run metadata reports test_used=false.
- Saved the aggregate output files in `docs/experiments/E01/`. We did not put player-level data or credentials on GitHub.

| Model | Mean AP ± SD | ROC-AUC | Accuracy | Precision | Recall | F1 | Brier | Mean fit (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Logistic Regression | 0.5793 ± 0.0514 | 0.7407 | 0.7579 | 0.6902 | 0.2866 | 0.4044 | 0.1720 | 0.0038 |
| XGBoost | 0.4921 ± 0.0433 | 0.6823 | 0.7219 | 0.5210 | 0.4082 | 0.4568 | 0.2057 | 0.0665 |
| Random Forest | 0.4664 ± 0.0394 | 0.6861 | 0.7082 | 0.4898 | 0.4299 | 0.4565 | 0.2017 | 0.1614 |
| Dummy | 0.2884 ± 0.0413 | 0.5000 | 0.7116 | 0.0000 | 0.0000 | 0.0000 | 0.2058 | 0.0003 |

### What we learned

- Logistic Regression ranked first by the prespecified primary metric, average precision, in all five validation folds. It improved AP by 0.2909 absolute over the dummy model (about twice the baseline AP) and by 0.0872 over untuned XGBoost. It also had highest mean ROC-AUC and lowest Brier score.
- At threshold 0.5, Logistic Regression has high precision but low recall. It misses about 71% of recorded returners in the validation folds. XGBoost and Random Forest achieved higher F1 and recall at the same threshold, despite worse ranking performance. A threshold can be selected using training validation predictions later if justified by the use case; do not tune it on the held-out test set.
- The scores vary from fold to fold. These were only our validation results, and we had not used the 790 test players yet.
- The 20 model fits took 1.160 seconds combined (not counting the entire program). For this small dataset we don't need the HPC yet. We'll time the tuning and AutoGluon experiments before deciding if we should run them there.

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
- Run the self-contained `notebooks/retention_baselines.ipynb` in Colab with the existing Flood-It ZIP. No BigQuery calls or Google Cloud credentials are needed. Alternatively run the Python scripts on a local CPU. We did not create new cloud resources or start any HPC jobs.

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

- I ran the notebook and uploaded `flood_it_audit.zip`. This resolves the Google authorization blocker for the initial export.
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
