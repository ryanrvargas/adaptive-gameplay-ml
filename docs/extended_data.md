# Getting more gameplay and ad-reward data

We finished our first model. Now I want to get closer to the reason I picked this project in the first place: seeing whether we can predict how someone plays a game and whether they are likely to earn an ad reward.

## What we are trying to predict

| Target | What we know before prediction | What we predict |
| --- | --- | --- |
| Future ad reward | First 24 hours of activity, sessions, scores, quickplay starts/wins/losses/resets/retries, extra steps and earlier ad rewards | At least one recorded ad_reward event within the next seven days |
| Quickplay outcome | The player's recorded starts, wins, losses, resets and retries strictly before the current attempt | Whether the next matched quickplay outcome is a win or loss |

The first target is **not** the probability a player accepts an ad offer. We don't have rejected offers or actual advertising revenue in this dataset. A reward event also depends on whether a player returns and whether an ad is offered.

For the quickplay table we match a start to the next decisive quickplay event from the same player. It has to be a recorded completion or failure on the same board, strictly later and within one hour. A retry, reset, another start, missing board, tied timestamp or other unresolved case is left unlabeled. We do not count those as losses. We can only predict outcomes for the matched subset; it might not represent all attempts.

The two new CSVs are separate from the completed E04 seven-day retention benchmark. The future reward count, outcome timestamp, match status, target, IDs and timestamps are not features. The original retention test results will not be used to change the original model.

## Get the export

1. Download [flood_it_extended_export.ipynb](../notebooks/flood_it_extended_export.ipynb).
2. Open it in Google Colab and run the first cell. Sign in with the account that owns our existing BigQuery sandbox and enter its project ID.
3. Run the next cell to check estimated scan size. The notebook stops above 25 GiB; check remaining free quota (don't enable billing).
4. Run the export cell and type RUN. It saves both tables and a manifest in `flood_it_extended.zip`.
5. Upload the ZIP to our project chat; keep the player-level data out of GitHub.

No new Google Cloud project is needed. The live queries haven't been run yet. The code passed a BigQuery-dialect parser check, but the BigQuery dry run will be the real validation.

## Review it before training

From the project root:

```powershell
python -m gameplay_ml.audit_extended data/raw/flood_it_extended.zip
```

This prints aggregate row counts, class balance, quickplay matching statuses and chronological split counts. The reward prediction uses a seven-day label gap; quickplay uses a one-hour gap. For quickplay, a player may have multiple attempts in both earlier and later periods; we will report that overlap and consider an additional player-disjoint test. The audit does not train a model.

If the reward target has too few positives in the training and validation periods, we'll report that and focus on quickplay. Before running new experiments, we'll record the exact feature sets, model selection metric, folds and test rules. We can then decide whether the larger quickplay table makes an HPC run worth doing.

No existing experiment results are replaced by this export.
