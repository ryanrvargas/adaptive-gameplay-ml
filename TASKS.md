# Project tasks

We will keep this file up to date as we work through the project. Start with the highest priority task that is ready. Add new tasks here as we find more things to work on, and write down what happened in `LOG.md` when we finish a task or run into a problem.

## P0 - Get the data and choose a model target

- [x] T01 - Set up the repository, proposal, task list and work log.
- [x] T02 - Prepare the queries and a script to audit the data.
- [x] T02a - Make a Colab notebook to export the audit results using a Google Cloud sandbox project.
- [x] T03 - Get access to the Flood-It! dataset through BigQuery. Ryan successfully exported `flood_it_audit.zip`.
- [x] T04 - Run the event and parameter inventory queries. Record actual event counts, date range, missing values and available ad, level and purchase events.
- [x] T05 - Check the number of players with enough data to measure retention. Choose seven-day return as the first target (3,947 players, 1,076 returned). Ad rewards and level outcomes are follow-up targets.
- [x] T06 - Export the candidate training table and review the features, target distribution and remaining missing values.

## P1 - Train and evaluate the models

- [x] T07 - Finalize the feature set and use a chronological train/test split. Reserve about 20% for testing, with a seven-day gap so training labels are known before the earliest test prediction. Keep player IDs and timestamps out of model inputs.
- [x] T08 - Train a simple baseline, Logistic Regression, Random Forest and XGBoost. Compare with five-fold cross-validation on the training data. E01 verified: Logistic Regression leads with mean AP 0.5793.
- [x] T09 - Tune hyperparameters using grid or random search. E02 completed: 72 configurations, 360 fits, tuned mean AP Logistic Regression 0.5814, Random Forest 0.5769, XGBoost 0.5715.
- [ ] T10 - Train AutoGluon with the same training data and compare all final models on the held-out data.
- [ ] T11 - Make the plots and save the evaluation metrics and best model configuration.
- [ ] T11a - After the first retention models, check an enriched export with quickplay wins, failures, retries and extra-step use. Assess a separate future ad-reward event target if enough positive players remain after the time split. Do not call this ad acceptance or revenue without offer and monetary data.

## P2 - Package the project

- [ ] T12 - Pin the Python dependencies and verify the Docker workflow.
- [ ] T13 - Write the final report (five pages or less) and make the submission ZIP.
- [ ] T14 - Check whether we need the HPC for longer model training and hyperparameter searches. If we do, test the cluster environment and run a small job first.

## P3 - If we have time

- [ ] T15 - Try an ensemble and compare it with the best individual model.
- [ ] T16 - Build a small original puzzle game to demonstrate how predictions could be used.
- [ ] T17 - Predict whether a player will make a purchase and their future spending if we have usable purchase data.
- [ ] T18 - Estimate combined purchase and ad revenue if both monetary values are available.

## Next up

T10. Run AutoGluon with the same purged validation folds, compare with E01/E02 and freeze model settings before evaluating the final 790 test players.
