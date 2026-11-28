"""Compare AutoGluon with the manual models on the same outer folds."""

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import random
from statistics import mean, stdev
from time import perf_counter

import numpy as np
import pandas as pd
from autogluon.tabular import TabularPredictor
from threadpoolctl import threadpool_limits

from gameplay_ml.prepare_retention import LABEL_WINDOW, load_players, split_players, summarize, validation_folds
from gameplay_ml.retention_audit import FEATURES, TARGET
from gameplay_ml.train_baselines import METRICS, SEED, score_predictions
from gameplay_ml.tune_retention import write_csv


# Explicit CPU-only portfolio, without GPU or neural-network dependencies.
# AutoGluon selects models and learns ensemble weights from its inner holdout.
PORTFOLIO = {
    'LR': {},
    'RF': {'n_estimators': 100},
    'XT': {'n_estimators': 100},
    'GBM': {'num_boost_round': 100},
    'CAT': {'iterations': 100},
    'XGB': {'n_estimators': 100},
}
INNER_FRACTION = 0.2


def frame(players):
    # Only the five allowed features and the label enter AutoGluon.
    return pd.DataFrame(players)[[*FEATURES, TARGET]].copy()


def fit_automl(players, path):
    # Never use the outer validation data to select a model or ensemble weights.
    fit_rows, gap_rows, tune_rows = split_players(players, test_fraction=INNER_FRACTION)
    random.seed(SEED)
    np.random.seed(SEED)
    predictor = TabularPredictor(label=TARGET, problem_type='binary',
                                 eval_metric='average_precision', path=str(path), verbosity=1)
    start = perf_counter()
    with threadpool_limits(limits=1):
        predictor.fit(train_data=frame(fit_rows), tuning_data=frame(tune_rows),
                      hyperparameters=PORTFOLIO, num_bag_folds=0, num_stack_levels=0,
                      dynamic_stacking=False, fit_weighted_ensemble=True,
                      calibrate_decision_threshold=False, num_cpus=1, num_gpus=0)
        selected = predictor.model_best
        board = predictor.leaderboard(silent=True)
        leaderboard = board.astype(object).where(pd.notna(board), None).to_dict(orient='records')
        # Refit on the inner training and tuning sets. Keep the gap excluded:
        # AutoGluon 1.5.0 did not use added gap rows in our refit check.
        refit = predictor.refit_full(model='best', set_best_to_refit_full=True,
                                     num_cpus=1, num_gpus=0)
    if selected not in refit or predictor.model_best != refit[selected]:
        raise RuntimeError('AutoGluon did not refit its selected model.')
    model_info = predictor.info()['model_info']
    refit_samples = {name: int(model_info[name]['num_samples'])
                     for name in refit.values() if name in model_info
                     and model_info[name].get('num_samples') is not None}
    # Check component models, not the ensemble weights learned on tuning rows.
    for name, count in refit_samples.items():
        if not name.startswith('WeightedEnsemble') and count != len(fit_rows) + len(tune_rows):
            raise RuntimeError(f'Unexpected full-refit row count for {name}: {count}')
    return predictor, {
        'inner_fit': summarize(fit_rows), 'inner_gap': summarize(gap_rows),
        'inner_tune': summarize(tune_rows), 'outer_train': summarize(players),
        'selected_model': selected, 'refit_model': predictor.model_best,
        'refit_mapping': refit, 'refit_samples': refit_samples,
        'fit_seconds': perf_counter() - start,
        'inner_leaderboard': leaderboard,
    }


def run_automl(split_dir, reference_dir, output):
    train_file = split_dir / 'train.csv'
    players = load_players(train_file)
    summary = json.loads((split_dir / 'split_summary.json').read_text())
    reference = json.loads((reference_dir / 'experiment.json').read_text())
    train_hash = hashlib.sha256(train_file.read_bytes()).hexdigest()
    if (train_hash != reference['train_csv_sha256']
            or summary['source_sha256'] != reference['source_sha256']
            or summary['features'] != FEATURES or reference['features'] != FEATURES
            or summary['target'] != TARGET or reference['target'] != TARGET
            or summary['train'] != summarize(players)
            or reference['primary_metric'] != 'average_precision'
            or reference['test_used'] is not False):
        raise ValueError('AutoML must use the same training data and target as E02.')
    cutoff = datetime.fromisoformat(summary['first_test_prediction_utc'])
    if players[-1]['cutoff_us'] + LABEL_WINDOW > round(cutoff.timestamp() * 1e6):
        raise ValueError('Training labels overlap the test window.')
    folds = validation_folds(players)
    expected = [(f['train_end'], f['validation_start'], f['validation_end'])
                for f in summary['folds']]
    if folds != expected or summary['folds'] != reference['folds']:
        raise ValueError('AutoML must use the same outer folds as E02.')

    output.mkdir(parents=True, exist_ok=False)
    scores, details = [], []
    for fold, (end, start, stop) in enumerate(folds, 1):
        print(f'AutoGluon fold {fold}: {end} training rows, {stop-start} validation rows', flush=True)
        predictor, info = fit_automl(players[:end], output / 'models' / f'fold_{fold}')
        validation = frame(players[start:stop])
        probabilities = predictor.predict_proba(validation[FEATURES])[1].to_numpy()
        row = {'model': 'AutoGluon', 'fold': fold, 'train_rows': end,
               'validation_rows': stop - start, 'fit_seconds': info['fit_seconds'],
               **score_predictions(validation[TARGET].to_numpy(), probabilities)}
        scores.append(row)
        details.append({'fold': fold, **info})
        print(f"  {info['selected_model']} -> AP={row['average_precision']:.4f}", flush=True)

    comparison = {'model': 'AutoGluon'}
    for metric in [*METRICS, 'fit_seconds']:
        values = [row[metric] for row in scores]
        comparison[metric + '_mean'] = mean(values)
        comparison[metric + '_std'] = stdev(values)
    write_csv(output / 'fold_metrics.csv', scores)
    write_csv(output / 'model_comparison.csv', [comparison])
    metadata = {
        'run_utc': datetime.now(timezone.utc).isoformat(), 'experiment': 'retention_automl',
        'python': platform.python_version(), 'platform': platform.platform(),
        'packages': {name: version(name) for name in ['autogluon.tabular', 'numpy', 'pandas',
                     'scipy', 'scikit-learn', 'xgboost', 'lightgbm', 'catboost', 'threadpoolctl']},
        'seed': SEED, 'cpu_threads': 1, 'source_sha256': summary['source_sha256'],
        'train_csv_sha256': train_hash, 'features': FEATURES, 'target': TARGET,
        'folds': summary['folds'], 'primary_metric': 'average_precision',
        'classification_threshold': 0.5, 'portfolio': PORTFOLIO,
        'inner_holdout_fraction': INNER_FRACTION, 'inner_gap_days': 7,
        'bagging': False, 'stacking': False, 'weighted_ensemble': True,
        'refit_on_inner_train_and_tune': True, 'inner_gap_excluded_from_refit': True,
        'per_fold_details': details, 'test_used': False,
    }
    # pandas represents missing leaderboard values as NaN; convert them to null.
    (output / 'experiment.json').write_text(json.dumps(metadata, indent=2, default=str, allow_nan=False) + '\n')
    print(f"Mean validation AP: {comparison['average_precision_mean']:.4f}")
    return comparison


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split-dir', type=Path, default=Path('data/processed/retention_split'))
    parser.add_argument('--reference-dir', type=Path, default=Path('docs/experiments/E02'))
    parser.add_argument('--output', type=Path, default=Path('results/retention_automl'))
    args = parser.parse_args()
    run_automl(args.split_dir, args.reference_dir, args.output)


if __name__ == '__main__':
    main()
