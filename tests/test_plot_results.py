"""Check that plotting uses only the archived aggregate results."""

import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


@unittest.skipUnless(importlib.util.find_spec('matplotlib'), 'Plotting dependencies not installed')
class PlotTests(unittest.TestCase):
    def test_archived_results_and_figure_generation(self):
        from gameplay_ml.plot_results import load_results, tuning_figure, holdout_figure, confusion_figure

        path = Path(__file__).resolve().parents[1] / 'docs' / 'experiments'
        e01, e02, e03, e04 = load_results(path)
        self.assertEqual(len(e04), 8)
        self.assertAlmostEqual(float(e03['AutoGluon']['average_precision_mean']), 0.5523848132987205)
        with TemporaryDirectory() as folder:
            output = Path(folder)
            tuning_figure(e01, e02, output)
            holdout_figure(e01, e02, e03, e04, output)
            confusion_figure(e04, output)
            self.assertEqual(len(list(output.glob('*.png'))), 3)
            self.assertEqual(len(list(output.glob('*.svg'))), 3)


if __name__ == '__main__':
    unittest.main()
