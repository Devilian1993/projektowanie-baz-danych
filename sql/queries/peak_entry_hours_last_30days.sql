SELECT
    EXTRACT(HOUR FROM entered_at) AS entry_hour,
    ROUND(COUNT(entry_id) * 100.0 / SUM(COUNT(entry_id)) OVER(), 2) || '%' AS percentage_of_entries,
    ROUND(COUNT(entry_id) / 30.0, 2) AS average_entries_per_day
FROM entry
WHERE entered_at >= CURRENT_DATE - INTERVAL '30 days'
  AND entered_at < CURRENT_DATE
  AND result = true
GROUP BY entry_hour
ORDER BY average_entries_per_day DESC, entry_hour ASC;
