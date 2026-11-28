import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from gameplay_ml.prepare_retention import (
    DAY_US, LABEL_WINDOW, TARGET, load_players, split_players, validation_folds,
)
from gameplay_ml.retention_audit import REQUIRED_COLUMNS


def player(number, day, label):
    return {
        'user_pseudo_id': str(number),
        'first_open_us': day * DAY_US,
        'cutoff_us': (day + 1) * DAY_US,
        'early_events': 4,
        'early_sessions': 1,
        'early_level_starts': 1,
        'early_level_ends': 1,
        'early_scores_posted': 0,
        TARGET: label,
    }


class PrepareRetentionTests(unittest.TestCase):
    def test_train_test_gap_and_ties(self):
        rows = [player(i, i + 1, i % 2) for i in range(100)]
        # Make two players share the first test timestamp.
        rows[79]['first_open_us'] = rows[80]['first_open_us']
        rows[79]['cutoff_us'] = rows[80]['cutoff_us']
        train, gap, test = split_players(rows)
        self.assertEqual(len(train) + len(gap) + len(test), len(rows))
        self.assertEqual(len(test), 21)
        self.assertLessEqual(train[-1]['cutoff_us'] + LABEL_WINDOW, test[0]['cutoff_us'])
        self.assertGreater(gap[0]['cutoff_us'] + LABEL_WINDOW, test[0]['cutoff_us'])

    def test_five_validation_folds(self):
        rows = [player(i, i + 1, i % 2) for i in range(150)]
        folds = validation_folds(rows)
        self.assertEqual(len(folds), 5)
        for end, start, stop in folds:
            self.assertLess(end, start)
            self.assertLess(start, stop)
            self.assertLessEqual(rows[end - 1]['cutoff_us'] + LABEL_WINDOW, rows[start]['cutoff_us'])
            self.assertEqual({row[TARGET] for row in rows[start:stop]}, {0, 1})
        self.assertEqual(folds[-1][2], len(rows))

    def test_load_and_validate(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'players.csv'
            rows = [player(1, 2, 'True'), player(2, 1, 'False')]
            with path.open('w', newline='') as output:
                writer = csv.DictWriter(output, fieldnames=REQUIRED_COLUMNS)
                writer.writeheader()
                writer.writerows(rows)
            loaded = load_players(path)
            self.assertEqual([row[TARGET] for row in loaded], [0, 1])
            with path.open('a', newline='') as output:
                csv.DictWriter(output, fieldnames=REQUIRED_COLUMNS).writerow(rows[0])
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                load_players(path)

    def test_reject_invalid_time_window(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'players.csv'
            row = player(1, 4, 1)
            row['cutoff_us'] += 1
            with path.open('w', newline='') as output:
                writer = csv.DictWriter(output, fieldnames=REQUIRED_COLUMNS)
                writer.writeheader()
                writer.writerow(row)
            with self.assertRaisesRegex(ValueError, '24-hour'):
                load_players(path)


if __name__ == '__main__':
    unittest.main()
