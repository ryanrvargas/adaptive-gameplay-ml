-- Get the overall size of the dataset. Keep this result for the report.
SELECT
  COUNT(*) AS total_events,
  COUNT(DISTINCT user_pseudo_id) AS unique_players,
  COUNT(DISTINCT event_date) AS days,
  MIN(event_date) AS first_date,
  MAX(event_date) AS last_date,
  COUNTIF(user_pseudo_id IS NULL OR TRIM(user_pseudo_id) = '') AS missing_player_ids,
  COUNTIF(event_timestamp IS NULL) AS missing_timestamps,
  COUNTIF(event_name IS NULL OR TRIM(event_name) = '') AS missing_event_names
FROM `firebase-public-project.analytics_153293282.events_2*`;
