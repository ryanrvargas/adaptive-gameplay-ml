"""Check whether the new gameplay and reward exports are usable for ML."""

import argparse
from collections import Counter
import csv
import io
import json
from pathlib import Path
from zipfile import ZipFile

from gameplay_ml.retention_audit import DAY_US, FEATURES


AD_FEATURES = [*FEATURES, 'early_quickplay_starts', 'early_quickplay_wins',
               'early_quickplay_failures', 'early_quickplay_retries',
               'early_quickplay_resets', 'early_extra_steps', 'early_ad_rewards']
LEVEL_FEATURES = ['prior_starts', 'prior_wins', 'prior_failures', 'prior_resets', 'prior_retries']
HOUR_US = 3_600_000_000
STATUSES = {'ambiguous_start_time', 'missing_start_board', 'no_later_event',
            'ambiguous_next_time', 'outside_one_hour', 'interrupted_or_restarted',
            'board_mismatch', 'win', 'loss'}


def read_rows(archive, name):
    with archive.open(name + '.csv') as stream:
        yield from csv.DictReader(io.TextIOWrapper(stream, encoding='utf-8-sig', newline=''))


def boolean(value):
    value = value.strip().lower()
    if value not in ('true', 'false', '1', '0'):
        raise ValueError('Invalid binary label.')
    return int(value in ('true', '1'))


def counts(rows):
    positives = sum(row[2] for row in rows)
    return {'rows': len(rows), 'positive': positives, 'negative': len(rows) - positives,
            'unique_players': len({row[1] for row in rows})}


def split_summary(rows, gap_us):
    # The actual test is kept aside. These are only size and class checks.
    if len(rows) < 2:
        return {'enough_rows': False}
    rows = sorted(rows)
    boundary = rows[int(len(rows) * .8)][0]
    train = [row for row in rows if row[0] < boundary and row[0] + gap_us <= boundary]
    gap = [row for row in rows if row[0] < boundary < row[0] + gap_us]
    test = [row for row in rows if row[0] >= boundary]
    assert len(train) + len(gap) + len(test) == len(rows)
    # Equal timestamps stay together. Repeated quickplay users may cross splits.
    return {'boundary_us': boundary, 'train': counts(train), 'excluded_gap': counts(gap),
            'test': counts(test), 'overlapping_players': len({x[1] for x in train} & {x[1] for x in test})}


def audit_ads(rows):
    eligible = []
    seen = set()
    reward_count = 0
    for row in rows:
        player = row['user_pseudo_id'].strip()
        first, cutoff = int(row['first_open_us']), int(row['cutoff_us'])
        if not player or player in seen or first <= 0 or cutoff - first != DAY_US:
            raise ValueError('Invalid or repeated ad-reward player/window.')
        seen.add(player)
        features = [int(row[name]) for name in AD_FEATURES]
        if any(value < 0 for value in features) or sum(features[1:]) >= features[0]:
            raise ValueError('Invalid ad-reward feature counts.')
        target = boolean(row['rewarded_next_7_days'])
        future = int(row['future_reward_count'])
        if future < 0 or int(future > 0) != target:
            raise ValueError('Reward count and label disagree.')
        reward_count += future
        eligible.append((cutoff, player, target))
    return {'cohort': counts(eligible), 'future_reward_events': reward_count,
            'split': split_summary(eligible, 7 * DAY_US)}


def audit_quickplay(rows):
    matched, statuses, seen = [], Counter(), set()
    players = set()
    for row in rows:
        player = row['user_pseudo_id'].strip()
        start = int(row['start_us'])
        status = row['match_status']
        if not player or start <= 0 or status not in STATUSES:
            raise ValueError('Invalid quickplay candidate.')
        players.add(player)
        statuses[status] += 1
        if any(int(row[name]) < 0 for name in LEVEL_FEATURES):
            raise ValueError('Negative quickplay history count.')
        if status in ('win', 'loss'):
            outcome = int(row['outcome_us'])
            label = int(row['won_attempt'])
            if not start < outcome <= start + HOUR_US or label != int(status == 'win'):
                raise ValueError('Invalid matched outcome.')
            if (player, start) in seen:
                raise ValueError('Repeated matched start.')
            seen.add((player, start))
            matched.append((start, player, label))
        elif row['outcome_us'] or row['won_attempt']:
            raise ValueError('Unmatched start should have no label.')
    return {'all_starts': sum(statuses.values()), 'all_players': len(players), 'match_status': dict(statuses),
            'matched': counts(matched), 'split': split_summary(matched, HOUR_US)}


def audit(path):
    with ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError('Corrupt ZIP.')
        manifest = json.loads(archive.read('manifest.json'))
        entries = {row['name']: row for row in manifest['queries']}
        if set(entries) != {'ad_reward_candidates', 'quickplay_candidates'}:
            raise ValueError('Expected both queries in the manifest.')
        ads = audit_ads(read_rows(archive, 'ad_reward_candidates'))
        levels = audit_quickplay(read_rows(archive, 'quickplay_candidates'))
        if ads['cohort']['rows'] != entries['ad_reward_candidates']['rows'] or levels['all_starts'] != entries['quickplay_candidates']['rows']:
            raise ValueError('CSV row counts disagree with the manifest.')
        billed = sum(row['billed_bytes'] for row in entries.values())
        if billed > 25 * 1024**3:
            raise ValueError('Recorded scan exceeds the export limit.')
    return {'ad_reward': ads, 'quickplay': levels, 'billed_bytes': billed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.source), indent=2))


if __name__ == '__main__':
    main()
