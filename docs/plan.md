# Project plan

## What we want to do

I want to see if we can predict whether a player will beat a level, watch a rewarded ad or return to the game based on the way they play. We will start with one prediction that we have enough data for and work from there. If we have time, we can put our models into a small original puzzle game.

## Step 1 - Get and review the data

We will start with [Google's Flood-It! dataset](https://developers.google.com/analytics/bigquery/app-gaming-demo-dataset). We have 114 days of game activity with some of the data obscured. First we need to see what each event means and whether the data has actual revenue amounts.

- Check the event names, dates, number of events, unique players and missing values.
- See what information we have for sessions, scores, levels, rewards and ads.
- Check if we can match a level attempt with its result.
- See if the data includes when a player was offered an ad and whether they took it. If it only contains ad rewards, we can predict whether a player will earn a future reward or how many they will earn.
- Make sure we have enough future data to see if a player came back within seven days.
- Write down what we are predicting, what data goes into the model and the time periods used for the features and labels.

By the end of this step we should know what we can predict, what features we can use and how many rows will be available.

## Step 2 - Set up the data and train models

Make a table with one row per player or level attempt. Only use information that would be there at the time of the prediction. Keep the timestamps and player IDs so we can split the data correctly. Leave the actual player IDs out of the model inputs.

Split the data into about 80% training and 20% testing. We will use five-fold cross-validation with the training data and keep the testing data for our final evaluation. If needed, split by player or date to avoid data leakage. Start with a simple baseline and try Logistic Regression, Random Forest and XGBoost for classification. For counts or amounts, try regression models.

## Step 3 - Tune the models and compare results

Use grid search or random search and keep track of the hyperparameters we tried and which settings did best. Compare the models before and after tuning and use AutoGluon to see how it compares using the same data and metric. We can use precision, recall, F1 and precision-recall AUC for classification and MAE for regression. Make plots of the results and include the instructions to reproduce them. If we have time, try ensembling.

## Step 4 - Demo if we have time

Make a small original puzzle game to show how the predictions could be used to adjust difficulty or offer optional rewards. If we want to prove that changing the difficulty or when ads appear improves the game, we would have to run a controlled experiment.

## Step 5 - Optional in-game purchases

If we get to this part, check if we have enough purchase data. Try predicting whether the player will buy something and how much they will spend. Compare gameplay by itself with gameplay and prior purchases. If we have actual dollar amounts for both advertising and purchases, we can estimate the total revenue.

## Class submission

We need to turn in the code, a way to reproduce the project and a report of five pages or less. Include what problem we are solving, what data we used, how we trained our models, the results before and after tuning, the best model settings, plots and how our models compared to AutoML. Put everything into a ZIP for Canvas.
