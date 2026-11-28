# Project work log

This is where we will keep track of what we worked on, what got in the way, how we handled it and what needs to be done next. Keep results from real data separate from test data.

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
