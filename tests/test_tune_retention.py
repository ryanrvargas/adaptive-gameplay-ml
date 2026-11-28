import unittest

import numpy as np
from sklearn.model_selection import ParameterGrid

from gameplay_ml.train_baselines import models
from gameplay_ml.tune_retention import GRIDS, search_model


class TuningTests(unittest.TestCase):
    def test_grid_sizes_and_baseline_settings(self):
        self.assertEqual([len(ParameterGrid(grid)) for grid in GRIDS.values()], [12, 24, 36])
        original = {
            'Logistic Regression': {'logisticregression__C': 1.0, 'logisticregression__class_weight': None},
            'Random Forest': {'n_estimators': 100, 'max_depth': None, 'min_samples_leaf': 1},
            'XGBoost': {'n_estimators': 100, 'max_depth': 6, 'learning_rate': 0.3, 'min_child_weight': 1},
        }
        for name, grid in GRIDS.items():
            self.assertIn(original[name], list(ParameterGrid(grid)))

    def test_search_uses_the_given_folds(self):
        # Synthetic features only: both classes occur in every fold.
        y = np.arange(30) % 2
        X = np.column_stack((y, np.arange(30)))
        model = next(model for name, model, _ in models() if name == 'Logistic Regression')
        grid = {'logisticregression__C': [0.1, 1.0]}
        folds = [(8, 10, 20), (18, 20, 30)]
        candidates, results, best, seconds = search_model('Logistic Regression', model, grid, X, y, folds)
        self.assertEqual(len(candidates), 2)
        self.assertEqual(len(results), 4)
        self.assertEqual({row['train_rows'] for row in results}, {8, 18})
        self.assertEqual({row['validation_rows'] for row in results}, {10})
        self.assertEqual(best['average_precision_mean'], max(row['average_precision_mean'] for row in candidates))
        self.assertGreaterEqual(seconds, 0)


if __name__ == '__main__':
    unittest.main()
