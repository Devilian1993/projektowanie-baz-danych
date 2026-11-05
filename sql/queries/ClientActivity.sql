WITH params AS (
    SELECT CAST(${Client id, e.g. 2} AS INTEGER) AS client_id,
           CAST(${Begin of the time range, in quotes, e.g. '2026-11-06 09:00:00', or null for any start time} AS TIMESTAMP) AS ts_begin,
           CAST(${End of the time range, in quotes, e.g. '2026-11-06 18:00:00', or null for any end time} AS TIMESTAMP) AS ts_end
)

SELECT 'Entry' AS activity_type,
        entry.entered_at AS start_time,
        entry.exited_at AS end_time

FROM params

JOIN client ON client.client_id = params.client_id
JOIN entry ON entry.account_id = client.account_id

WHERE entry.result AND
      (params.ts_end IS NULL OR entry.entered_at <= params.ts_end) AND
      -- if no exit time then look at enter time, otherwise look at exit time
      (params.ts_begin IS NULL OR COALESCE(entry.exited_at, entry.entered_at) >= params.ts_begin)

UNION ALL

SELECT 'Station reservation' AS activity_type,
        station_reservation.reserved_from AS start_time,
        station_reservation.reserved_to AS end_time

FROM params

JOIN personal_training ON personal_training.client_id = params.client_id
JOIN station_reservation ON station_reservation.training_id = personal_training.training_id

WHERE (NOT personal_training.is_cancelled)
  AND station_reservation.is_active
  AND (params.ts_end IS NULL OR station_reservation.reserved_from <= params.ts_end)
  AND (params.ts_begin IS NULL OR station_reservation.reserved_to >= params.ts_begin)

UNION ALL

SELECT 'Personal training' AS activity_type,
        personal_training.starts_at AS start_time,
        personal_training.ends_at AS end_time

FROM params

JOIN personal_training ON personal_training.client_id = params.client_id

WHERE (NOT personal_training.is_cancelled) AND
      (params.ts_end IS NULL OR personal_training.starts_at <= params.ts_end) AND
      (params.ts_begin IS NULL OR personal_training.ends_at >= params.ts_begin)

UNION ALL

SELECT 'Group class' AS activity_type,
        group_class.starts_at AS start_time,
        group_class.starts_at + class_type.duration_minutes * INTERVAL '1 minute' AS end_time

FROM params

JOIN class_enrollment ON class_enrollment.client_id = params.client_id
JOIN group_class ON group_class.class_id = class_enrollment.class_id
JOIN class_type ON class_type.class_type_id = group_class.class_type_id

WHERE (NOT group_class.is_cancelled) AND
      (params.ts_end IS NULL OR group_class.starts_at <= params.ts_end) AND
      (params.ts_begin IS NULL OR group_class.starts_at + class_type.duration_minutes * INTERVAL '1 minute' >= params.ts_begin)

order by start_time, end_time
