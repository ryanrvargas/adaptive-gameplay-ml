"""Evaluate the frozen models on the held-out players. Never tune on this split."""

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
from time import perf_counter

import numpy as np
from sklearn.metrics import confusion_matrix
from threadpoolctl import threadpool_limits

from gameplay_ml.prepare_retention import LABEL_WINDOW, load_players, split_players, summarize
from gameplay_ml.retention_audit import FEATURES, TARGET
from gameplay_ml.train_baselines import SEED, models, score_predictions
from gameplay_ml.tune_retention import write_csv


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def arrays(rows):
    return np.array([[row[name] for name in FEATURES] for row in rows], dtype=float), np.array([row[TARGET] for row in rows])


def evaluate(split_dir, source, protocol_path, output, group):
    protocol = json.loads(protocol_path.read_text())
    assert protocol['features'] == FEATURES and protocol['target'] == TARGET
    assert protocol['seed'] == SEED and protocol['classification_threshold'] == 0.5
    if sha(source) != protocol['source_sha256'] or sha(split_dir / 'train.csv') != protocol['train_csv_sha256']:
        raise ValueError('Input data does not match the frozen experiment.')
    expected_train, gap, expected_test = split_players(load_players(source))
    train = load_players(split_dir / 'train.csv')
    test = load_players(split_dir / 'test.csv')
    if train != expected_train or test != expected_test:
        raise ValueError('Split files do not match the original chronological split.')
    assert (len(train), len(gap), len(test)) == (protocol['train_players'], protocol['excluded_players'], protocol['test_players'])
    assert train[-1]['cutoff_us'] + LABEL_WINDOW <= test[0]['cutoff_us']
    X, y = arrays(train)
    X_test, y_test = arrays(test)
    expected_packages = protocol[group]['packages']
    packages = {name: version(name) for name in expected_packages}
    if packages != expected_packages:
        raise ValueError(f'Use the pinned {group} environment: {packages}')
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    details = {}

    def record(name, probabilities, seconds, fitted_rows):
        tn, fp, fn, tp = confusion_matrix(y_test, probabilities >= 0.5, labels=[0, 1]).ravel()
        rows.append({'model': name, 'train_rows': fitted_rows, 'test_rows': len(test),
                     'fit_seconds': seconds, **score_predictions(y_test, probabilities),
                     'tn': int(tn), 'fp': int(fp), 'fn': int(fn), 'tp': int(tp)})
        print(f"{name}: AP={rows[-1]['average_precision']:.4f}", flush=True)

    if group == 'manual':
        from sklearn.base import clone
        import joblib

        for name, model, settings in models():
            if name != 'Dummy' and settings != protocol['manual']['baseline_settings'][name]:
                raise ValueError('Baseline settings differ from frozen protocol.')
            variants = [('baseline', {})] if name == 'Dummy' else [('untuned', {}), ('tuned', protocol['manual']['best_parameters'][name])]
            for variant, params in variants:
                label = name if name == 'Dummy' else f'{name} ({variant})'
                estimator = clone(model).set_params(**params)
                with threadpool_limits(limits=1):
                    started = perf_counter()
                    estimator.fit(X, y)
                    seconds = perf_counter() - started
                    probabilities = estimator.predict_proba(X_test)[:, 1]
                record(label, probabilities, seconds, len(train))
                details[label] = {'base_settings': settings, 'overrides': params}
                if label == protocol['validation_selected_model']:
                    joblib.dump(estimator, output / 'selected_model.joblib')
    else:
        from gameplay_ml.train_automl import PORTFOLIO, INNER_FRACTION, fit_automl, frame

        assert PORTFOLIO == protocol['automl']['portfolio'] and INNER_FRACTION == protocol['automl']['inner_holdout_fraction']
        predictor, details = fit_automl(train, output / 'models')
        names = {row['model'] for row in details['inner_leaderboard']}
        expected = {'LinearModel', 'RandomForest', 'ExtraTrees', 'LightGBM', 'CatBoost', 'XGBoost'}
        if not expected <= names:
            raise RuntimeError(f'AutoGluon skipped models: {expected - names}')
        probabilities = predictor.predict_proba(frame(test)[FEATURES])[1].to_numpy()
        count = details['inner_fit']['players'] + details['inner_tune']['players']
        record('AutoGluon', probabilities, details['fit_seconds'], count)

    write_csv(output / 'test_metrics.csv', rows)
    metadata = {'experiment': 'E04_final_holdout', 'group': group,
                'run_utc': datetime.now(timezone.utc).isoformat(), 'python': platform.python_version(),
                'platform': platform.platform(), 'packages': packages, 'protocol_sha256': sha(protocol_path),
                'source_sha256': sha(source), 'train_csv_sha256': sha(split_dir / 'train.csv'),
                'test_csv_sha256': sha(split_dir / 'test.csv'), 'validation_selected_model': protocol['validation_selected_model'],
                'train': summarize(train), 'excluded': summarize(gap), 'test': summarize(test),
                'test_used': True, 'test_used_for_selection': False, 'details': details}
    (output / 'experiment.json').write_text(json.dumps(metadata, indent=2, default=str, allow_nan=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('group', choices=['manual', 'automl'])
    parser.add_argument('source', type=Path)
    parser.add_argument('--split-dir', type=Path, default=Path('data/processed/retention_split'))
    parser.add_argument('--protocol', type=Path, default=Path('docs/experiments/E04/protocol.json'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    evaluate(args.split_dir, args.source, args.protocol,
             args.output or Path('results/retention_final') / args.group, args.group)


if __name__ == '__main__':
    main()
