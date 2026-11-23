-- First see what events we have and how many players we have for each event.
-- Check the estimated amount of data BigQuery will read before running this.
SELECT
  event_name,
  COUNT(*) AS event_count,
  COUNT(DISTINCT user_pseudo_id) AS unique_players,
  COUNTIF(user_pseudo_id IS NULL) AS missing_player_ids,
  MIN(event_date) AS first_event_date,
  MAX(event_date) AS last_event_date
FROM `firebase-public-project.analytics_153293282.events_*`
GROUP BY event_name
ORDER BY event_count DESC;
