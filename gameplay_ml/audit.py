"""Inspect a local export of gameplay events before building training data."""

import argparse
import csv
from collections import Counter
from pathlib import Path


REQUIRED_COLUMNS = {'user_pseudo_id', 'event_timestamp', 'event_name'}


def audit_events(path):
    event_counts = Counter()
    players = set()
    missing = Counter()
    total = 0

    with path.open(encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file)
        absent = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if absent:
            raise ValueError(f"Missing columns: {', '.join(sorted(absent))}")

        for row in reader:
            total += 1
            for column in REQUIRED_COLUMNS:
                if not (row[column] or '').strip():
                    missing[column] += 1

            player = (row['user_pseudo_id'] or '').strip()
            event = (row['event_name'] or '').strip()
            if player:
                players.add(player)
            if event:
                event_counts[event] += 1

    print(f'Rows: {total:,}')
    print(f'Unique players: {len(players):,}')
    print('\nMissing required fields:')
    for column in sorted(REQUIRED_COLUMNS):
        print(f'  {column}: {missing[column]:,}')
    print('\nEvent counts:')
    for event, count in event_counts.most_common():
        print(f'  {event}: {count:,}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_path', type=Path, help='Path to an exported event CSV')
    args = parser.parse_args()
    try:
        audit_events(args.csv_path)
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(1, f'Audit failed: {error}\n')


if __name__ == '__main__':
    main()
