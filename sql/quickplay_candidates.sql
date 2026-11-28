-- One candidate per recorded quickplay start. Match only unambiguous outcomes.
-- If a new attempt, retry or reset comes first, do not assume a win or loss.
WITH raw_events AS (
  SELECT user_pseudo_id, event_timestamp, event_name,
    ARRAY(SELECT DISTINCT param.value.string_value FROM UNNEST(event_params) AS param
      WHERE param.key = 'board' AND param.value.string_value IS NOT NULL
        AND TRIM(param.value.string_value) != '') AS boards
  FROM `firebase-public-project.analytics_153293282.events_2*`
  WHERE user_pseudo_id IS NOT NULL AND TRIM(user_pseudo_id) != ''
    AND event_timestamp IS NOT NULL
    AND event_name IN ('level_start_quickplay', 'level_complete_quickplay',
        'level_fail_quickplay', 'level_retry_quickplay', 'level_reset_quickplay')
), events AS (
  SELECT user_pseudo_id, event_timestamp, event_name,
    IF(ARRAY_LENGTH(boards) = 1, boards[SAFE_OFFSET(0)], NULL) AS board,
    COUNT(*) OVER (PARTITION BY user_pseudo_id, event_timestamp) AS same_time_events
  FROM raw_events
), ordered AS (
  SELECT *,
    LEAD(event_timestamp) OVER sequence AS next_timestamp,
    LEAD(event_name) OVER sequence AS next_name,
    LEAD(board) OVER sequence AS next_board,
    LEAD(same_time_events) OVER sequence AS next_same_time_events,
    COUNTIF(event_name = 'level_start_quickplay') OVER history AS prior_starts,
    COUNTIF(event_name = 'level_complete_quickplay') OVER history AS prior_wins,
    COUNTIF(event_name = 'level_fail_quickplay') OVER history AS prior_failures,
    COUNTIF(event_name = 'level_reset_quickplay') OVER history AS prior_resets,
    COUNTIF(event_name = 'level_retry_quickplay') OVER history AS prior_retries
  FROM events
  WINDOW sequence AS (PARTITION BY user_pseudo_id ORDER BY event_timestamp, event_name, board),
    history AS (PARTITION BY user_pseudo_id ORDER BY event_timestamp
      RANGE BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)
), attempts AS (
  SELECT *, CASE
    WHEN same_time_events != 1 THEN 'ambiguous_start_time'
    WHEN board IS NULL THEN 'missing_start_board'
    WHEN next_timestamp IS NULL THEN 'no_later_event'
    WHEN next_same_time_events != 1 OR next_timestamp <= event_timestamp THEN 'ambiguous_next_time'
    WHEN next_timestamp - event_timestamp > 3600000000 THEN 'outside_one_hour'
    WHEN next_name NOT IN ('level_complete_quickplay', 'level_fail_quickplay') THEN 'interrupted_or_restarted'
    WHEN next_board IS NULL OR next_board != board THEN 'board_mismatch'
    WHEN next_name = 'level_complete_quickplay' THEN 'win'
    ELSE 'loss' END AS match_status
  FROM ordered WHERE event_name = 'level_start_quickplay'
)
SELECT user_pseudo_id, event_timestamp AS start_us,
  prior_starts, prior_wins, prior_failures, prior_resets, prior_retries,
  match_status,
  IF(match_status IN ('win', 'loss'), next_timestamp, NULL) AS outcome_us,
  CASE WHEN match_status = 'win' THEN 1 WHEN match_status = 'loss' THEN 0 ELSE NULL END AS won_attempt
FROM attempts
ORDER BY start_us, user_pseudo_id, match_status;
