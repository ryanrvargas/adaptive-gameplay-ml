-- Predict whether a new player gets at least one recorded ad reward in days 2-8.
-- Only the first 24 hours are used for features. No ad offers or revenue are inferred.
WITH events AS (
  SELECT user_pseudo_id, event_name, event_timestamp
  FROM `firebase-public-project.analytics_153293282.events_2*`
  WHERE user_pseudo_id IS NOT NULL AND TRIM(user_pseudo_id) != ''
    AND event_timestamp IS NOT NULL
), first_open AS (
  SELECT user_pseudo_id, MIN(event_timestamp) AS first_open_us
  FROM events WHERE event_name = 'first_open' GROUP BY user_pseudo_id
), data_end AS (
  SELECT MAX(event_timestamp) AS last_event_us FROM events
), eligible AS (
  SELECT f.user_pseudo_id, f.first_open_us,
    f.first_open_us + 86400000000 AS cutoff_us,
    f.first_open_us + 691200000000 AS label_end_us
  FROM first_open AS f CROSS JOIN data_end AS d
  WHERE f.first_open_us + 691200000000 <= d.last_event_us
)
SELECT p.user_pseudo_id, p.first_open_us, p.cutoff_us,
  COUNTIF(e.event_timestamp < p.cutoff_us) AS early_events,
  COUNTIF(e.event_timestamp < p.cutoff_us AND e.event_name = 'session_start') AS early_sessions,
  COUNTIF(e.event_timestamp < p.cutoff_us AND e.event_name = 'level_start') AS early_level_starts,
  COUNTIF(e.event_timestamp < p.cutoff_us AND e.event_name = 'level_end') AS early_level_ends,
  COUNTIF(e.event_timestamp < p.cutoff_us AND e.event_name = 'post_score') AS early_scores_posted,
  COUNTIF(e.event_timestamp < p.cutoff_us AND e.event_name = 'level_start_quickplay') AS early_quickplay_starts,
  COUNTIF(e.event_timestamp < p.cutoff_us AND e.event_name = 'level_complete_quickplay') AS early_quickplay_wins,
  COUNTIF(e.event_timestamp < p.cutoff_us AND e.event_name = 'level_fail_quickplay') AS early_quickplay_failures,
  COUNTIF(e.event_timestamp < p.cutoff_us AND e.event_name = 'level_retry_quickplay') AS early_quickplay_retries,
  COUNTIF(e.event_timestamp < p.cutoff_us AND e.event_name = 'level_reset_quickplay') AS early_quickplay_resets,
  COUNTIF(e.event_timestamp < p.cutoff_us AND e.event_name = 'use_extra_steps') AS early_extra_steps,
  COUNTIF(e.event_timestamp < p.cutoff_us AND e.event_name = 'ad_reward') AS early_ad_rewards,
  COUNTIF(e.event_timestamp >= p.cutoff_us AND e.event_name = 'ad_reward') AS future_reward_count,
  COUNTIF(e.event_timestamp >= p.cutoff_us AND e.event_name = 'ad_reward') > 0 AS rewarded_next_7_days
FROM eligible AS p JOIN events AS e
  ON p.user_pseudo_id = e.user_pseudo_id
  AND e.event_timestamp >= p.first_open_us AND e.event_timestamp < p.label_end_us
GROUP BY p.user_pseudo_id, p.first_open_us, p.cutoff_us
ORDER BY p.first_open_us, p.user_pseudo_id;
