"""Tests requiring the separate AutoML environment."""

import importlib.util
import unittest

from gameplay_ml.retention_audit import DAY_US, FEATURES, TARGET


@unittest.skipUnless(importlib.util.find_spec('autogluon'), 'AutoGluon environment not installed')
class AutoMLTests(unittest.TestCase):
    def test_feature_isolation(self):
        from gameplay_ml.train_automl import frame

        data = {name: 1 for name in FEATURES}
        data.update({TARGET: 0, 'user_pseudo_id': 'example', 'cutoff_us': DAY_US})
        self.assertEqual(list(frame([data]).columns), [*FEATURES, TARGET])

    def test_inner_split_with_purge(self):
        from gameplay_ml.prepare_retention import LABEL_WINDOW, split_players

        rows = [{'user_pseudo_id': str(i), 'cutoff_us': (i+1)*DAY_US, TARGET: i%2}
                for i in range(100)]
        train, gap, tune = split_players(rows, test_fraction=0.2)
        self.assertLessEqual(train[-1]['cutoff_us'] + LABEL_WINDOW, tune[0]['cutoff_us'])
        self.assertEqual(len(train) + len(gap) + len(tune), len(rows))


if __name__ == '__main__':
    unittest.main()
