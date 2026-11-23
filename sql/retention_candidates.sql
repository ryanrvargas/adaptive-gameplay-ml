-- A possible first training table. Run the inventory before using this.
-- One row per player with an observed first_open and eight days of follow-up.
-- Features use the first 24 hours. The target uses the next seven days.
WITH events AS (
  SELECT user_pseudo_id, event_name, event_timestamp
  FROM `firebase-public-project.analytics_153293282.events_2*`
  WHERE user_pseudo_id IS NOT NULL
    AND TRIM(user_pseudo_id) != ''
    AND event_timestamp IS NOT NULL
),
first_open AS (
  SELECT user_pseudo_id, MIN(event_timestamp) AS first_open_us
  FROM events
  WHERE event_name = 'first_open'
  GROUP BY user_pseudo_id
),
data_end AS (
  SELECT MAX(event_timestamp) AS last_event_us FROM events
),
eligible_players AS (
  SELECT
    f.user_pseudo_id,
    f.first_open_us,
    f.first_open_us + 86400000000 AS cutoff_us,
    f.first_open_us + 691200000000 AS label_end_us
  FROM first_open AS f
  CROSS JOIN data_end AS d
  WHERE f.first_open_us + 691200000000 <= d.last_event_us
)
SELECT
  p.user_pseudo_id,
  p.first_open_us,
  p.cutoff_us,
  COUNTIF(e.event_timestamp < p.cutoff_us) AS early_events,
  COUNTIF(e.event_name = 'session_start' AND e.event_timestamp < p.cutoff_us) AS early_sessions,
  COUNTIF(e.event_name = 'level_start' AND e.event_timestamp < p.cutoff_us) AS early_level_starts,
  COUNTIF(e.event_name = 'level_end' AND e.event_timestamp < p.cutoff_us) AS early_level_ends,
  COUNTIF(e.event_name = 'post_score' AND e.event_timestamp < p.cutoff_us) AS early_scores_posted,
  COUNTIF(e.event_name = 'session_start' AND e.event_timestamp >= p.cutoff_us) > 0 AS returned_next_7_days
FROM eligible_players AS p
JOIN events AS e
  ON p.user_pseudo_id = e.user_pseudo_id
  AND e.event_timestamp >= p.first_open_us
  AND e.event_timestamp < p.label_end_us
GROUP BY p.user_pseudo_id, p.first_open_us, p.cutoff_us
ORDER BY p.first_open_us, p.user_pseudo_id;
