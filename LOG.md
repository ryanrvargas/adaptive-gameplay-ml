# Project work log

This is where we will keep track of what we worked on, what got in the way, how we handled it and what needs to be done next. Keep results from real data separate from test data.

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
