"""Compare untuned retention models on the five training-data folds."""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import platform
from importlib.metadata import version
from pathlib import Path
from statistics import mean, stdev
from time import perf_counter

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, average_precision_score, balanced_accuracy_score,
    brier_score_loss, f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits
from xgboost import XGBClassifier

from gameplay_ml.prepare_retention import LABEL_WINDOW, load_players, summarize, validation_folds
from gameplay_ml.retention_audit import FEATURES, TARGET


SEED = 42
METRICS = ['average_precision', 'roc_auc', 'accuracy', 'balanced_accuracy',
           'precision', 'recall', 'f1', 'brier_score']


def models():
    # Fixed starting settings, before any hyperparameter search.
    dummy = {'strategy': 'prior'}
    logistic = {'C': 1.0, 'solver': 'lbfgs', 'max_iter': 1000, 'random_state': SEED}
    forest = {'n_estimators': 100, 'random_state': SEED, 'n_jobs': 1}
    boosted = {'n_estimators': 100, 'max_depth': 6, 'learning_rate': 0.3,
               'objective': 'binary:logistic', 'eval_metric': 'logloss',
               'random_state': SEED, 'n_jobs': 1, 'tree_method': 'hist'}
    return [
        ('Dummy', DummyClassifier(**dummy), dummy),
        ('Logistic Regression', make_pipeline(StandardScaler(), LogisticRegression(**logistic)),
         {'preprocessing': 'StandardScaler fitted within each fold', **logistic}),
        ('Random Forest', RandomForestClassifier(**forest), forest),
        ('XGBoost', XGBClassifier(**boosted), boosted),
    ]


def score_predictions(labels, probabilities):
    # Class 1 means the player returned. Use the same threshold for every model.
    predictions = (probabilities >= 0.5).astype(int)
    return {
        'average_precision': float(average_precision_score(labels, probabilities)),
        'roc_auc': float(roc_auc_score(labels, probabilities)),
        'accuracy': float(accuracy_score(labels, predictions)),
        'balanced_accuracy': float(balanced_accuracy_score(labels, predictions)),
        'precision': float(precision_score(labels, predictions, zero_division=0)),
        'recall': float(recall_score(labels, predictions, zero_division=0)),
        'f1': float(f1_score(labels, predictions, zero_division=0)),
        'brier_score': float(brier_score_loss(labels, probabilities)),
    }


def run_baselines(split_dir, output):
    # Do not load test.csv. It is reserved for the final experiment.
    train_file = split_dir / 'train.csv'
    train = load_players(train_file)
    summary = json.loads((split_dir / 'split_summary.json').read_text())
    if summary['features'] != FEATURES or summary['target'] != TARGET:
        raise ValueError('The split uses a different feature set or target.')
    if summary['train'] != summarize(train):
        raise ValueError('The training rows do not match the split summary.')
    cutoff = datetime.fromisoformat(summary['first_test_prediction_utc'])
    if train[-1]['cutoff_us'] + LABEL_WINDOW > round(cutoff.timestamp() * 1e6):
        raise ValueError('Training labels overlap the test prediction window.')
    folds = validation_folds(train)
    expected = [(f['train_end'], f['validation_start'], f['validation_end'])
                for f in summary['folds']]
    if folds != expected:
        raise ValueError('Validation fold boundaries do not match the saved split.')

    X = np.array([[row[name] for name in FEATURES] for row in train], dtype=float)
    y = np.array([row[TARGET] for row in train], dtype=int)
    settings = {name: params for name, _, params in models()}
    results = []
    for number, (end, start, stop) in enumerate(folds, 1):
        for name, model, _ in models():
            # Build a fresh model each time. Preprocessing is fitted only on training rows.
            with threadpool_limits(limits=1):
                began = perf_counter()
                model.fit(X[:end], y[:end])
                seconds = perf_counter() - began
                probabilities = model.predict_proba(X[start:stop])[:, 1]
            scores = score_predictions(y[start:stop], probabilities)
            results.append({'model': name, 'fold': number, 'train_rows': end,
                            'validation_rows': stop - start,
                            'validation_return_rate': float(y[start:stop].mean()),
                            'fit_seconds': seconds, **scores})
            print(f"{name:20s} fold {number}: AP={scores['average_precision']:.4f}")

    comparisons = []
    for name in settings:
        model_rows = [row for row in results if row['model'] == name]
        item = {'model': name}
        for metric in [*METRICS, 'fit_seconds']:
            values = [row[metric] for row in model_rows]
            item[metric + '_mean'] = mean(values)
            item[metric + '_std'] = stdev(values)
        comparisons.append(item)
    comparisons.sort(key=lambda row: row['average_precision_mean'], reverse=True)

    # Everything saved here is aggregate. No IDs, labels or individual predictions.
    output.mkdir(parents=True, exist_ok=False)
    for filename, rows in [('fold_metrics.csv', results), ('model_comparison.csv', comparisons)]:
        with (output / filename).open('w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    metadata = {
        'run_utc': datetime.now(timezone.utc).isoformat(),
        'experiment': 'retention_untuned_baselines',
        'python': platform.python_version(),
        'platform': platform.platform(),
        'packages': {name: version(name) for name in
                     ['numpy', 'scipy', 'scikit-learn', 'xgboost', 'threadpoolctl']},
        'seed': SEED,
        'cpu_threads': 1,
        'source_sha256': summary['source_sha256'],
        'train_csv_sha256': hashlib.sha256(train_file.read_bytes()).hexdigest(),
        'features': FEATURES,
        'target': TARGET,
        'folds': summary['folds'],
        'primary_metric': 'average_precision',
        'classification_threshold': 0.5,
        'model_settings': settings,
        'test_used': False,
    }
    (output / 'experiment.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print('\nValidation comparison (mean average precision):')
    for row in comparisons:
        print(f"{row['model']:20s} {row['average_precision_mean']:.4f} "
              f"(SD {row['average_precision_std']:.4f})")
    return comparisons


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split-dir', type=Path, default=Path('data/processed/retention_split'))
    parser.add_argument('--output', type=Path, default=Path('results/retention_baselines'))
    args = parser.parse_args()
    run_baselines(args.split_dir, args.output)


if __name__ == '__main__':
    main()
