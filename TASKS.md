# Project tasks

We will keep this file up to date as we work through the project. Start with the highest priority task that is ready. Add new tasks here as we find more things to work on, and write down what happened in `LOG.md` when we finish a task or run into a problem.

## P0 - Get the data and choose a model target

- [x] T01 - Set up the repository, proposal, task list and work log.
- [x] T02 - Prepare the queries and a script to audit the data.
- [ ] T03 - Get access to the Flood-It! dataset through BigQuery. **Blocked: need a BigQuery-enabled Google Cloud project.**
- [ ] T04 - Run the event and parameter inventory queries. Record actual event counts, date range, missing values and available ad, level and purchase events.
- [ ] T05 - Check the number of players with enough data to measure retention. Review reward and level labels and choose the first prediction target.
- [ ] T06 - Export the candidate training table and review the features, target distribution and remaining missing values.

## P1 - Train and evaluate the models

- [ ] T07 - Finalize the table and split the data without leakage. Reserve about 20% for testing.
- [ ] T08 - Train a simple baseline, Logistic Regression, Random Forest and XGBoost. Compare with five-fold cross-validation on the training data.
- [ ] T09 - Tune hyperparameters using grid or random search. Save the settings and compare results before and after tuning.
- [ ] T10 - Train AutoGluon with the same training data and compare all final models on the held-out data.
- [ ] T11 - Make the plots and save the evaluation metrics and best model configuration.

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

T03 and T04. Get into BigQuery, check the project and query estimates, and run the inventory. Once we see the actual results, we can decide which model to build first.
