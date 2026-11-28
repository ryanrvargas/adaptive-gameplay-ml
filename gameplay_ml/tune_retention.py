"""Tune the three retention classifiers without using the test set."""

import argparse
import csv
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
from statistics import mean, stdev
from time import perf_counter

import numpy as np
from sklearn.model_selection import GridSearchCV, ParameterGrid
from threadpoolctl import threadpool_limits

from gameplay_ml.prepare_retention import LABEL_WINDOW, load_players, summarize, validation_folds
from gameplay_ml.retention_audit import FEATURES, TARGET
from gameplay_ml.train_baselines import METRICS, SEED, models, score_predictions


# Include the original settings in each grid so tuning can keep them if necessary.
GRIDS = {
    'Logistic Regression': {
        'logisticregression__C': [0.001, 0.01, 0.1, 1.0, 10.0, 100.0],
        'logisticregression__class_weight': [None, 'balanced'],
    },
    'Random Forest': {
        'n_estimators': [100, 200],
        'max_depth': [None, 3, 6, 10],
        'min_samples_leaf': [1, 5, 15],
    },
    'XGBoost': {
        'n_estimators': [100, 200],
        'max_depth': [2, 3, 6],
        'learning_rate': [0.03, 0.1, 0.3],
        'min_child_weight': [1, 5],
    },
}


def score_model(model, X, y):
    # Use exactly the same scoring and probability threshold as E01.
    return score_predictions(y, model.predict_proba(X)[:, 1])


def search_model(name, model, grid, X, y, folds):
    cv = [(np.arange(end), np.arange(start, stop)) for end, start, stop in folds]
    search = GridSearchCV(model, grid, scoring=score_model, cv=cv,
                          refit=False, n_jobs=1, error_score='raise')
    started = perf_counter()
    with threadpool_limits(limits=1):
        search.fit(X, y)
    elapsed = perf_counter() - started

    candidates = []
    fold_rows = []
    for index, params in enumerate(search.cv_results_['params']):
        item = {'model': name, 'candidate': index + 1,
                'parameters': json.dumps(params, sort_keys=True)}
        for metric in METRICS:
            values = [float(search.cv_results_[f'split{i}_test_{metric}'][index])
                      for i in range(len(folds))]
            item[metric + '_mean'] = mean(values)
            # sklearn reports population SD; E01 used sample SD, so match that.
            item[metric + '_std'] = stdev(values)
        item['fit_seconds_mean'] = float(search.cv_results_['mean_fit_time'][index])
        candidates.append(item)
        for fold, (end, start, stop) in enumerate(folds, 1):
            fold_rows.append({'model': name, 'candidate': index + 1, 'fold': fold,
                              'train_rows': end, 'validation_rows': stop - start,
                              **{metric: float(search.cv_results_[f'split{fold-1}_test_{metric}'][index])
                                 for metric in METRICS}})

    # The primary metric was chosen before looking at the results. Ties use the
    # first candidate in sklearn's deterministic ParameterGrid order.
    best = max(candidates, key=lambda item: item['average_precision_mean'])
    return candidates, fold_rows, best, elapsed


def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_tuning(split_dir, baseline_dir, output):
    # Reproduce and verify the exact E01 training split; never load test.csv.
    train_file = split_dir / 'train.csv'
    train = load_players(train_file)
    summary = json.loads((split_dir / 'split_summary.json').read_text())
    baseline = json.loads((baseline_dir / 'experiment.json').read_text())
    train_hash = hashlib.sha256(train_file.read_bytes()).hexdigest()
    if (baseline['experiment'] != 'retention_untuned_baselines'
            or baseline['test_used'] is not False
            or baseline['primary_metric'] != 'average_precision'
            or baseline['classification_threshold'] != 0.5
            or baseline['seed'] != SEED):
        raise ValueError('The baseline experiment is not comparable.')
    if (summary['source_sha256'] != baseline['source_sha256']
            or train_hash != baseline['train_csv_sha256']
            or summary['features'] != FEATURES or baseline['features'] != FEATURES
            or summary['target'] != TARGET or baseline['target'] != TARGET
            or summary['train'] != summarize(train)):
        raise ValueError('The E02 training data must match E01 exactly.')
    cutoff = datetime.fromisoformat(summary['first_test_prediction_utc'])
    if train[-1]['cutoff_us'] + LABEL_WINDOW > round(cutoff.timestamp() * 1e6):
        raise ValueError('Training labels overlap the test window.')
    folds = validation_folds(train)
    expected = [(f['train_end'], f['validation_start'], f['validation_end'])
                for f in summary['folds']]
    if folds != expected or summary['folds'] != baseline['folds']:
        raise ValueError('Validation folds must match E01.')

    package_names = ['numpy', 'scipy', 'scikit-learn', 'xgboost', 'threadpoolctl']
    packages = {name: version(name) for name in package_names}
    if packages != baseline['packages']:
        print('Warning: package versions differ from E01. This is recorded in experiment.json.')

    with (baseline_dir / 'model_comparison.csv').open(newline='', encoding='utf-8') as file:
        before = {row['model']: row for row in csv.DictReader(file)}
    X = np.array([[row[name] for name in FEATURES] for row in train], dtype=float)
    y = np.array([row[TARGET] for row in train], dtype=int)
    if output.exists():
        raise FileExistsError(f'{output} already exists. Choose another --output folder.')

    candidates, fold_rows, comparison, best_params, search_seconds = [], [], [], {}, {}
    baseline_settings = {}
    for name, model, settings in models():
        if name not in GRIDS:
            continue
        baseline_settings[name] = settings
        count = len(ParameterGrid(GRIDS[name]))
        print(f'{name}: {count} configurations x {len(folds)} folds', flush=True)
        rows, scores, best, elapsed = search_model(name, model, GRIDS[name], X, y, folds)
        candidates.extend(rows)
        fold_rows.extend(scores)
        best_params[name] = json.loads(best['parameters'])
        search_seconds[name] = elapsed
        item = {'model': name, 'candidate': best['candidate'], 'parameters': best['parameters']}
        for metric in METRICS:
            old = float(before[name][metric + '_mean'])
            new = best[metric + '_mean']
            item[metric + '_baseline'] = old
            item[metric + '_tuned'] = new
            item[metric + '_delta'] = new - old
            item[metric + '_tuned_std'] = best[metric + '_std']
        comparison.append(item)
        print(f"  AP: {item['average_precision_baseline']:.4f} -> "
              f"{item['average_precision_tuned']:.4f} ({elapsed:.1f}s search)", flush=True)

    comparison.sort(key=lambda row: row['average_precision_tuned'], reverse=True)
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / 'candidate_metrics.csv', candidates)
    write_csv(output / 'fold_metrics.csv', fold_rows)
    write_csv(output / 'tuned_comparison.csv', comparison)
    metadata = {
        'run_utc': datetime.now(timezone.utc).isoformat(),
        'experiment': 'retention_grid_search',
        'python': platform.python_version(), 'platform': platform.platform(),
        'packages': packages, 'same_packages_as_e01': packages == baseline['packages'],
        'seed': SEED, 'cpu_threads': 1,
        'source_sha256': summary['source_sha256'], 'train_csv_sha256': train_hash,
        'features': FEATURES, 'target': TARGET, 'folds': summary['folds'],
        'primary_metric': 'average_precision', 'classification_threshold': 0.5,
        'search_grids': GRIDS, 'base_settings': baseline_settings,
        'candidate_count': len(candidates), 'fold_fit_count': len(fold_rows),
        'best_parameters': best_params, 'search_seconds': search_seconds,
        'test_used': False,
    }
    (output / 'experiment.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(f'Finished {len(fold_rows)} fits. Results saved to {output}.')
    return comparison


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split-dir', type=Path, default=Path('data/processed/retention_split'))
    parser.add_argument('--baseline-dir', type=Path, default=Path('docs/experiments/E01'))
    parser.add_argument('--output', type=Path, default=Path('results/retention_tuning'))
    args = parser.parse_args()
    run_tuning(args.split_dir, args.baseline_dir, args.output)


if __name__ == '__main__':
    main()
