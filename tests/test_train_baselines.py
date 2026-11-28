"""Small tests for the baseline experiment, using synthetic data only."""
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from gameplay_ml.retention_audit import DAY_US, REQUIRED_COLUMNS, TARGET
from gameplay_ml.prepare_retention import prepare
from gameplay_ml.train_baselines import run_baselines, score_predictions


class BaselineTests(unittest.TestCase):
    def test_perfect_predictions(self):
        scores = score_predictions(np.array([0, 1, 0, 1]), np.array([0.1, 0.8, 0.2, 0.9]))
        for metric in ('average_precision', 'roc_auc', 'accuracy', 'precision', 'recall', 'f1'):
            self.assertEqual(scores[metric], 1.0)

    def test_all_models_without_test_file(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'synthetic.csv'
            with source.open('w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=REQUIRED_COLUMNS)
                writer.writeheader()
                for index in range(150):
                    label = index % 2
                    writer.writerow({
                        'user_pseudo_id': str(index),
                        'first_open_us': (index + 1) * DAY_US,
                        'cutoff_us': (index + 2) * DAY_US,
                        'early_events': 5 + label,
                        'early_sessions': 1, 'early_level_starts': 1,
                        'early_level_ends': 1, 'early_scores_posted': label,
                        TARGET: label,
                    })
            split = root / 'split'
            prepare(source, split)
            # The baseline script must work without the held-out data.
            (split / 'test.csv').unlink()
            output = root / 'results'
            comparison = run_baselines(split, output)
            self.assertEqual(len(comparison), 4)
            with (output / 'fold_metrics.csv').open(newline='') as file:
                self.assertEqual(len(list(csv.DictReader(file))), 20)
            self.assertFalse(json.loads((output / 'experiment.json').read_text())['test_used'])


if __name__ == '__main__':
    unittest.main()
