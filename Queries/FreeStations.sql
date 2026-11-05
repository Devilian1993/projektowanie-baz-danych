WITH initial_params AS (
    SELECT CAST(${Room name, in quotes e.g. 'Strefa Cardio' or null to search every room} AS VARCHAR(100)) AS room_name,
           CAST(${Begin of the time range, in quotes, e.g. '2026-11-06 09:00:00', or null for current hour} AS TIMESTAMP) AS ts_begin,
           CAST(${End of the time range, in quotes, e.g. '2026-11-06 18:00:00', or null for begin + 1 day} AS TIMESTAMP) AS ts_end,
           CAST(${Equipment category, in quotes, e.g. 'Bieżnie', or null for any} AS VARCHAR(100)) AS equipment_category,
           CAST(${Time slot interval, in quotes , e.g. '1 hour' or null for entire time range slot} AS INTERVAL) AS slot_length
),
-- calculating ts_begin if NULL
begin_params AS (
	SELECT room_name,
	       equipment_category,
	       slot_length,
           COALESCE(ts_begin, date_trunc('hour', LOCALTIMESTAMP)) AS ts_begin,
           ts_end
    FROM initial_params
),
-- calculating ts_end if NULL
end_params AS (
    SELECT room_name,
           equipment_category,
           ts_begin,
           COALESCE(ts_end, ts_begin + INTERVAL '1 day') AS ts_end,
           slot_length
    FROM begin_params
),
-- calculating slot_length if NULL
params AS (
    SELECT room_name,
           equipment_category,
           ts_begin,
           ts_end,
           COALESCE(slot_length, ts_end - ts_begin) AS slot_length
    FROM end_params
),
slots AS (
    SELECT generate_series(params.ts_begin,
                           params.ts_end - params.slot_length,
                           params.slot_length) AS slot_start
    FROM params
    WHERE params.ts_end > params.ts_begin
      AND params.slot_length > INTERVAL '0'
)

SELECT room.name AS room_name,
       station.station_id,
       station.name AS station_name,
       equipment_category.name AS category_name,
       machine.machine_id,
       machine.tech_condition,
       machine_model.manufacturer,
       machine_model.model,
       slots.slot_start,
       slots.slot_start + params.slot_length AS slot_end
FROM station

CROSS JOIN slots
CROSS JOIN params

JOIN room ON room.room_id = station.room_id
LEFT JOIN machine ON machine.station_id = station.station_id
LEFT JOIN machine_model ON machine_model.model_id = machine.model_id
LEFT JOIN equipment_category ON equipment_category.category_id = machine_model.category_id

WHERE (params.room_name IS NULL OR room.name = params.room_name)
    AND room.is_active
    AND slots.slot_start >= slots.slot_start::date + room.opening_time
    -- assuming it is not open across midnight
    AND slots.slot_start + params.slot_length <= slots.slot_start::date + room.closing_time
    AND station.is_available
    AND (params.equipment_category IS NULL OR equipment_category.name = params.equipment_category)

-- no group classes for that room
AND NOT EXISTS (
        SELECT 1
        FROM group_class
        JOIN class_type ON class_type.class_type_id = group_class.class_type_id
        WHERE group_class.room_id = station.room_id
          AND NOT group_class.is_cancelled
          -- negation of starts_at >= slot_end
          AND group_class.starts_at < slots.slot_start + params.slot_length
          -- negation of ends_at <= slot_start
          AND group_class.starts_at + class_type.duration_minutes * INTERVAL '1 minute' > slots.slot_start
)

-- no valid reservations
AND NOT EXISTS (
      SELECT 1
      FROM station_reservation
      JOIN personal_training ON personal_training.training_id = station_reservation.training_id
      WHERE station_reservation.station_id = station.station_id
        AND station_reservation.is_active
        AND NOT personal_training.is_cancelled
        -- negation of reserved_from >= slot_end
        AND station_reservation.reserved_from < slots.slot_start + params.slot_length
        -- negation of reserved_to <= slot_start
        AND station_reservation.reserved_to > slots.slot_start
)

ORDER BY room_name, station.station_id, equipment_category.name, machine.machine_id, slots.slot_start
