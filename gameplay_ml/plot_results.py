"""Create paper figures from the archived retention experiment summaries."""

import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


MODELS = ['Logistic Regression', 'Random Forest', 'XGBoost']
LABELS = ['Logistic\nregression', 'Random\nforest', 'XGBoost']
BLUE = '#245a85'
TEAL = '#147d73'
GRAY = '#a8b6c3'
INK = '#24384b'


def read_models(path):
    with path.open(newline='', encoding='utf-8-sig') as file:
        reader = list(csv.DictReader(file))
    rows = {row['model']: row for row in reader}
    if len(rows) != len(reader):
        raise ValueError(f'Duplicate model in {path}')
    return rows


def load_results(root):
    e01 = read_models(root / 'E01' / 'model_comparison.csv')
    e02 = read_models(root / 'E02' / 'tuned_comparison.csv')
    e03 = read_models(root / 'E03' / 'model_comparison.csv')
    e04 = read_models(root / 'E04' / 'manual' / 'test_metrics.csv')
    e04.update(read_models(root / 'E04' / 'automl' / 'test_metrics.csv'))
    for name in MODELS:
        if abs(float(e01[name]['average_precision_mean']) - float(e02[name]['average_precision_baseline'])) > 1e-10:
            raise ValueError(f'Baseline mismatch for {name}')
    for row in e04.values():
        if int(row['test_rows']) != 790 or sum(int(row[key]) for key in ['tn', 'fp', 'fn', 'tp']) != 790:
            raise ValueError('Unexpected held-out cohort size.')
    return e01, e02, e03, e04


def style(ax, title, ylabel):
    ax.set_title(title, loc='left', weight='bold', pad=14, color=INK)
    ax.set_ylabel(ylabel)
    ax.spines[['top', 'right']].set_visible(False)
    ax.grid(axis='y', color='#e3e8eb', linewidth=0.7)
    ax.set_axisbelow(True)


def save(fig, output, name):
    fig.savefig(output / (name + '.svg'), bbox_inches='tight', metadata={'Date': None})
    fig.savefig(output / (name + '.png'), dpi=300, bbox_inches='tight')
    plt.close(fig)


def tuning_figure(e01, e02, output):
    x = np.arange(len(MODELS))
    old = [float(e01[name]['average_precision_mean']) for name in MODELS]
    new = [float(e02[name]['average_precision_tuned']) for name in MODELS]
    old_sd = [float(e01[name]['average_precision_std']) for name in MODELS]
    new_sd = [float(e02[name]['average_precision_tuned_std']) for name in MODELS]
    fig, ax = plt.subplots(figsize=(7.1, 3.8), layout='constrained')
    style(ax, 'Validation performance before and after tuning', 'Mean average precision (AP)')
    ax.bar(x - .18, old, .34, color=GRAY, label='Untuned', yerr=old_sd, capsize=3)
    ax.bar(x + .18, new, .34, color=BLUE, label='Tuned', yerr=new_sd, capsize=3)
    baseline = float(e01['Dummy']['average_precision_mean'])
    ax.axhline(baseline, color='#596875', linestyle='--', linewidth=1.2, label='Dummy AP')
    for i, (a, b, sd) in enumerate(zip(old, new, new_sd)):
        ax.text(i+.18, b+sd+.012, f'+{b-a:.3f}', ha='center', fontsize=9, color=INK, weight='bold')
    ax.set_xticks(x, LABELS)
    ax.set_ylim(0, .80)
    ax.legend(loc='upper left', frameon=False, ncol=3, fontsize=9)
    save(fig, output, 'validation_tuning')


def holdout_figure(e01, e02, e03, e04, output):
    names = [name + ' (tuned)' for name in MODELS] + ['AutoGluon']
    validation = [float(e02[name]['average_precision_tuned']) for name in MODELS] + [float(e03['AutoGluon']['average_precision_mean'])]
    test = [float(e04[name]['average_precision']) for name in names]
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(7.1, 3.8), layout='constrained')
    style(ax, 'Validation and held-out test average precision', 'Average precision (AP)')
    ax.bar(x-.18, validation, .34, color=GRAY, label='Validation mean')
    ax.bar(x+.18, test, .34, color=TEAL, label='Held-out test')
    ax.axhline(float(e01['Dummy']['average_precision_mean']), color='#687581', linestyle=':', label='Validation dummy')
    ax.axhline(float(e04['Dummy']['average_precision']), color=INK, linestyle='--', label='Test dummy')
    for i, score in enumerate(test):
        ax.text(i+.18, score+.013, f'{score:.3f}', ha='center', fontsize=9, color=INK)
    ax.set_xticks(x, LABELS + ['AutoGluon'])
    ax.set_ylim(0, .76)
    ax.legend(loc='upper left', frameon=False, ncol=2, fontsize=9)
    save(fig, output, 'validation_vs_test')


def confusion_figure(e04, output):
    names = [name + ' (tuned)' for name in MODELS] + ['AutoGluon']
    fig, axes = plt.subplots(2, 2, figsize=(7.1, 5.5), layout='constrained')
    fig.suptitle('Held-out classification at a 0.5 threshold', fontsize=13, weight='bold', color=INK)
    for ax, name, label in zip(axes.flat, names, ['Logistic regression (selected)', 'Random forest', 'XGBoost', 'AutoGluon']):
        row = e04[name]
        counts = np.array([[int(row['tn']), int(row['fp'])], [int(row['fn']), int(row['tp'])]])
        rates = counts / counts.sum(axis=1, keepdims=True)
        ax.imshow(rates, vmin=0, vmax=1, cmap='Blues')
        for a in range(2):
            for b in range(2):
                ax.text(b, a, f'{counts[a,b]}\n({rates[a,b]:.1%})', ha='center', va='center',
                        color='white' if rates[a,b] > .55 else INK, fontsize=10, weight='bold')
        ax.set_title(label, fontsize=10, weight='bold', color=INK)
        ax.set_xticks([0, 1], ['No return', 'Return'])
        ax.set_yticks([0, 1], ['No return', 'Return'])
        ax.set_xlabel('Predicted', fontsize=9)
        ax.set_ylabel('Actual', fontsize=9)
        ax.tick_params(length=0, labelsize=9)
    save(fig, output, 'test_confusion_matrices')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiments', type=Path, default=Path('docs/experiments'))
    parser.add_argument('--output', type=Path, default=Path('results/figures'))
    args = parser.parse_args()
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10, 'svg.fonttype': 'none',
                         'svg.hashsalt': 'retention_e04', 'axes.labelcolor': INK, 'text.color': INK})
    args.output.mkdir(parents=True, exist_ok=False)
    e01, e02, e03, e04 = load_results(args.experiments)
    tuning_figure(e01, e02, args.output)
    holdout_figure(e01, e02, e03, e04, args.output)
    confusion_figure(e04, args.output)
    print(f'Saved three figures as PNG and SVG in {args.output}')


if __name__ == '__main__':
    main()
