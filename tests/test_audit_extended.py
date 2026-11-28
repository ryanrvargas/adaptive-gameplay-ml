import unittest

from gameplay_ml.audit_extended import AD_FEATURES, LEVEL_FEATURES, DAY_US, HOUR_US, audit_ads, audit_quickplay, split_summary


class ExtendedAuditTests(unittest.TestCase):
    def test_reward_labels(self):
        row = {name: '0' for name in AD_FEATURES}
        row.update(user_pseudo_id='a', first_open_us='1', cutoff_us=str(DAY_US+1),
                   early_events='1', future_reward_count='2', rewarded_next_7_days='True')
        result = audit_ads([row])
        self.assertEqual(result['cohort']['positive'], 1)
        self.assertEqual(result['future_reward_events'], 2)
        with self.assertRaisesRegex(ValueError, 'disagree'):
            audit_ads([{**row, 'future_reward_count': '0'}])
        with self.assertRaisesRegex(ValueError, 'repeated'):
            audit_ads([row, row])

    def test_quickplay_unmatched_not_loss(self):
        row = {name: '0' for name in LEVEL_FEATURES}
        row.update(user_pseudo_id='a', start_us='1', outcome_us='2', match_status='win', won_attempt='1')
        unmatched = {**row, 'start_us': '3', 'outcome_us': '', 'match_status': 'board_mismatch', 'won_attempt': ''}
        result = audit_quickplay([row, unmatched])
        self.assertEqual(result['all_starts'], 2)
        self.assertEqual(result['matched']['rows'], 1)
        self.assertEqual(result['matched']['negative'], 0)
        with self.assertRaisesRegex(ValueError, 'no label'):
            audit_quickplay([{**unmatched, 'won_attempt': '0'}])

    def test_hour_gap_and_timestamp_ties(self):
        rows = [(i * HOUR_US, str(i), i % 2) for i in range(1, 11)]
        rows.extend([(9*HOUR_US, 'same', 1), (9*HOUR_US-1, 'gap', 0)])
        result = split_summary(rows, HOUR_US)
        self.assertEqual(result['boundary_us'], 9*HOUR_US)
        self.assertEqual(result['test']['rows'], 3)
        self.assertEqual(result['excluded_gap']['rows'], 1)
        self.assertEqual(result['train']['rows'], 8)


if __name__ == '__main__':
    unittest.main()
