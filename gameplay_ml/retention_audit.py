"""Check the candidate retention table before we train a model."""

import argparse
import csv
from collections import Counter
from pathlib import Path


FEATURES = [
    'early_events',
    'early_sessions',
    'early_level_starts',
    'early_level_ends',
    'early_scores_posted',
]
TARGET = 'returned_next_7_days'
DAY_US = 86_400_000_000
REQUIRED_COLUMNS = ['user_pseudo_id', 'first_open_us', 'cutoff_us', *FEATURES, TARGET]


def audit_retention(path):
    players = set()
    missing = Counter()
    invalid = Counter()
    nonzero = Counter()
    targets = Counter()
    total = 0
    duplicates = 0

    with path.open(encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file)
        absent = set(REQUIRED_COLUMNS) - set(reader.fieldnames or [])
        if absent:
            raise ValueError(f"Missing columns: {', '.join(sorted(absent))}")

        for row in reader:
            total += 1
            for column in REQUIRED_COLUMNS:
                if not (row[column] or '').strip():
                    missing[column] += 1

            # We should only have one row for each player.
            player = (row['user_pseudo_id'] or '').strip()
            if player:
                if player in players:
                    duplicates += 1
                players.add(player)

            # Make sure the feature window is exactly 24 hours.
            try:
                first_open = int(row['first_open_us'])
                cutoff = int(row['cutoff_us'])
                if first_open <= 0 or cutoff - first_open != DAY_US:
                    invalid['time window'] += 1
            except (TypeError, ValueError):
                invalid['time window'] += 1

            for feature in FEATURES:
                try:
                    count = int(row[feature])
                    if count < 0 or (feature == 'early_events' and count == 0):
                        invalid[feature] += 1
                    elif count > 0:
                        nonzero[feature] += 1
                except (TypeError, ValueError):
                    invalid[feature] += 1

            # BigQuery may export the Boolean label as true/false or 1/0.
            label = (row[TARGET] or '').strip().lower()
            if label in ('true', '1'):
                targets['returned'] += 1
            elif label in ('false', '0'):
                targets['did not return'] += 1
            else:
                invalid[TARGET] += 1

    print(f'Rows: {total:,}')
    print(f'Unique players: {len(players):,}')
    print(f'Duplicate player rows: {duplicates:,}')
    print('\nTarget counts:')
    for label in ('returned', 'did not return'):
        print(f'  {label}: {targets[label]:,}')
    valid_labels = sum(targets.values())
    if valid_labels:
        print(f'Return rate: {targets["returned"] / valid_labels:.2%}')

    print('\nRows with a nonzero feature:')
    for feature in FEATURES:
        print(f'  {feature}: {nonzero[feature]:,}')

    print('\nMissing values:')
    for column in REQUIRED_COLUMNS:
        print(f'  {column}: {missing[column]:,}')
    print('\nInvalid values:')
    for column, count in invalid.items():
        print(f'  {column}: {count:,}')
    if not invalid:
        print('  None')

    if not total or duplicates or missing or invalid:
        raise ValueError('Fix the table issues and run the audit again.')
    if not targets['returned'] or not targets['did not return']:
        raise ValueError('We need examples of both outcomes for classification.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_path', type=Path)
    args = parser.parse_args()
    try:
        audit_retention(args.csv_path)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f'Audit failed: {error}\n')


if __name__ == '__main__':
    main()
