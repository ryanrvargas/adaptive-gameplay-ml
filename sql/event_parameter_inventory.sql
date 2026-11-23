-- Find out what extra information is recorded with each event.
SELECT
  event_name,
  param.key AS parameter_name,
  COUNT(*) AS parameter_count,
  COUNTIF(param.value.string_value IS NOT NULL) AS string_values,
  COUNTIF(param.value.int_value IS NOT NULL) AS integer_values,
  COUNTIF(param.value.float_value IS NOT NULL) AS float_values,
  COUNTIF(param.value.double_value IS NOT NULL) AS double_values
FROM `firebase-public-project.analytics_153293282.events_2*`,
UNNEST(event_params) AS param
GROUP BY event_name, parameter_name
ORDER BY event_name, parameter_count DESC;
