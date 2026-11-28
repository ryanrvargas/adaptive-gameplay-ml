"""Prepare chronological train/test sets for the retention model."""

import argparse
from bisect import bisect_left, bisect_right
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

from gameplay_ml.retention_audit import DAY_US, FEATURES, REQUIRED_COLUMNS, TARGET


LABEL_WINDOW = 7 * DAY_US


def load_players(path):
    # Accept the Colab export directly so we do not need another download.
    if path.suffix.lower() == '.zip':
        with ZipFile(path) as archive:
            lines = archive.read('retention_candidates.csv').decode('utf-8-sig').splitlines()
    else:
        lines = path.read_text(encoding='utf-8-sig').splitlines()

    reader = csv.DictReader(lines)
    if set(REQUIRED_COLUMNS) - set(reader.fieldnames or []):
        raise ValueError('The retention table is missing required columns.')

    players = []
    seen = set()
    for raw in reader:
        player = raw['user_pseudo_id'].strip()
        if not player or player in seen:
            raise ValueError('Missing or duplicate player ID.')
        seen.add(player)
        row = {'user_pseudo_id': player}
        for name in ['first_open_us', 'cutoff_us', *FEATURES]:
            row[name] = int(raw[name])
        if row['first_open_us'] <= 0 or row['cutoff_us'] - row['first_open_us'] != DAY_US:
            raise ValueError('Invalid 24-hour feature window.')
        if any(row[name] < 0 for name in FEATURES):
            raise ValueError('Negative feature count.')
        # Total early events include first_open as well as the specific events.
        if sum(row[name] for name in FEATURES[1:]) >= row['early_events']:
            raise ValueError('Specific event counts cannot account for all early events.')
        label = raw[TARGET].strip().lower()
        if label not in ('true', 'false', '1', '0'):
            raise ValueError('Invalid retention label.')
        row[TARGET] = int(label in ('true', '1'))
        players.append(row)

    # Keep players who have the same prediction time together.
    return sorted(players, key=lambda row: (row['cutoff_us'], row['user_pseudo_id']))


def require_both_classes(rows, name):
    if {row[TARGET] for row in rows} != {0, 1}:
        raise ValueError(f'{name} needs examples of both outcomes.')


def split_players(players, test_fraction=0.2):
    if not 0 < test_fraction < 1 or len(players) < 2:
        raise ValueError('Need a nonempty chronological training and testing split.')
    times = [row['cutoff_us'] for row in players]
    # Use the newest 20% for testing. Move timestamp ties into the test set.
    index = int(len(players) * (1 - test_fraction))
    start = bisect_left(times, times[index])
    # Only train on players whose entire label window has ended before testing.
    end = bisect_right(times, times[start] - LABEL_WINDOW, hi=start)
    train, gap, test = players[:end], players[end:start], players[start:]
    require_both_classes(train, 'Training set')
    require_both_classes(test, 'Test set')
    return train, gap, test


def validation_folds(train, n_folds=5):
    # Use expanding training windows and later validation blocks. Never use test rows.
    times = [row['cutoff_us'] for row in train]
    if n_folds < 1 or len(train) <= n_folds:
        raise ValueError('Not enough training rows for validation.')
    bounds = [0]
    for fold in range(1, n_folds + 1):
        index = len(train) * fold // (n_folds + 1)
        bounds.append(bisect_left(times, times[index]))
    bounds.append(len(train))

    folds = []
    for fold in range(1, n_folds + 1):
        start, stop = bounds[fold], bounds[fold + 1]
        end = bisect_right(times, times[start] - LABEL_WINDOW, hi=start)
        require_both_classes(train[:end], f'Fold {fold} training')
        require_both_classes(train[start:stop], f'Fold {fold} validation')
        # The indices are zero-based; the end index is not included.
        folds.append((end, start, stop))
    return folds


def summarize(rows):
    returned = sum(row[TARGET] for row in rows)
    return {'players': len(rows), 'returned': returned, 'did_not_return': len(rows) - returned}


def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def prepare(source, output):
    players = load_players(source)
    train, gap, test = split_players(players)
    folds = validation_folds(train)
    summary = {
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'features': FEATURES,
        'target': TARGET,
        'label_window_days': 7,
        'first_test_prediction_utc': datetime.fromtimestamp(test[0]['cutoff_us'] / 1e6, timezone.utc).isoformat(),
        'all_players': summarize(players),
        'train': summarize(train),
        'gap': summarize(gap),
        'test': summarize(test),
        'folds': [
            {'fold': number, 'train_end': end, 'validation_start': start, 'validation_end': stop,
             'train': summarize(train[:end]), 'validation': summarize(train[start:stop])}
            for number, (end, start, stop) in enumerate(folds, 1)
        ],
    }
    # Keep player-level files local, and do not overwrite an earlier experiment.
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / 'train.csv', train)
    write_csv(output / 'test.csv', test)
    (output / 'split_summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', type=Path, default=Path('data/processed/retention_split'))
    args = parser.parse_args()
    prepare(args.source, args.output)


if __name__ == '__main__':
    main()
