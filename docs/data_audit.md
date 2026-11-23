# Getting the data and reviewing it

We are starting with Google's [Flood-It! sample dataset](https://developers.google.com/analytics/bigquery/app-gaming-demo-dataset). The source tables are in `firebase-public-project.analytics_153293282`. The event data is obfuscated, so we need to check what is actually available and what the values mean before training anything.

## Step 1 - Run the queries in BigQuery

Open the dataset using Google's documentation. We need access to a Google Cloud project with BigQuery enabled. The free BigQuery sandbox is an option. Check the estimated bytes before running each query and stay within the free or authorized quota. We do not need to set up paid billing for this audit.

Run these in order and save the results as CSVs under `data/raw/`:

| Query | Output file | What it tells us |
| --- | --- | --- |
| `sql/dataset_summary.sql` | `dataset_summary.csv` | Total events, players, dates and missing fields |
| `sql/event_inventory.sql` | `event_inventory.csv` | How many of each event we have |
| `sql/event_parameter_inventory.sql` | `event_parameter_inventory.csv` | Which extra values come with each event |

Record the query date and key findings in `LOG.md`. The queries select the daily event tables and only the columns needed for the audit. We will inspect the event names before making assumptions about rewarded ads or purchases.

## Step 2 - Check if retention is a good first target

Once the event inventory confirms `first_open` and `session_start`, run `sql/retention_candidates.sql`. Export the result to `data/processed/retention_candidates.csv`.

- The table has one row per player with a recorded `first_open` event and enough observation time at the end of the data.
- We use the first 24 hours for model inputs. The target is whether the player starts a session during the next seven days.
- We can use the early events, sessions, level starts, level ends and score event counts as starting features. Check their real counts first. We can add quickplay events or reward events after verifying the names and meaning.
- Keep `user_pseudo_id`, `first_open_us` and `cutoff_us` for splitting and checking the data. Exclude them from the model feature list.
- Check the number of eligible players, the number who returned, any missing timestamps and the coverage of the date range. Since players can return without a logged session, this measures recorded session starts. Missing `first_open` events also limit the cohort, so we will report that.

Run this command on the exported table to check the counts, duplicates, missing values and the 24-hour feature window:

```sh
python -m gameplay_ml.retention_audit data/processed/retention_candidates.csv
```

Check dates and possible gaps in the source data separately using the SQL summary and inventory. A successful audit tells us the table is formatted as expected and has both outcomes. We still need to review how representative the players and their events are.

Before committing to retention, compare how much usable data we have for the other outcomes. If the inventory has reward events but no record of ad offers, we can predict future reward events. To predict acceptance probability, we would need both accepted and declined offers. If there are enough matched level attempts and outcomes, we can try level success as well.

## Step 3 - Run a local CSV check

If we export individual event rows with `user_pseudo_id`, `event_timestamp` and `event_name`, we can run:

```sh
python -m gameplay_ml.audit data/raw/events.csv
```

Keep exported player-level and event-level data local. Record aggregate counts and findings in the project log. Once the query results are available, we will update the task list and choose one target for the first training experiment.

## Sources

- [Flood-It! dataset documentation](https://developers.google.com/analytics/bigquery/app-gaming-demo-dataset)
- [Google Analytics BigQuery export schema](https://support.google.com/analytics/answer/7029846)
