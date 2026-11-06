SELECT
    m.machine_id,
    m.serial_number,
    mm.manufacturer,
    mm.model,
    mm.name                                        AS model_name,
    ec.name                                        AS category_name,
    m.tech_condition,
    COALESCE(s.name, '— storage / service —')      AS station_name,
    r.name                                         AS room_name,
    m.maintenance_date                             AS last_maintenance_date,
    sr.request_id                                  AS open_request_id,
    sr.request_type,
    sr.reported_at,
    CASE
        WHEN sr.request_id    IS NULL THEN 'no open request'
        WHEN sr.technician_id IS NULL THEN 'unassigned'
        WHEN sr.start_date    IS NULL THEN 'assigned, not started'
        ELSE 'in progress'
    END                                            AS request_status,
    tech.first_name || ' ' || tech.last_name       AS technician_name,
    date_trunc('minute', CURRENT_TIMESTAMP - sr.reported_at) AS waiting_time
FROM machine m
JOIN machine_model      mm ON mm.model_id    = m.model_id
JOIN equipment_category ec ON ec.category_id = mm.category_id
LEFT JOIN station       s  ON s.station_id   = m.station_id
LEFT JOIN room          r  ON r.room_id      = s.room_id
LEFT JOIN LATERAL (         -- oldest open request for the machine
    SELECT q.*
    FROM service_request q
    WHERE q.machine_id = m.machine_id
      AND q.end_date IS NULL
    ORDER BY q.reported_at
    LIMIT 1
) sr ON TRUE
LEFT JOIN technician    tech ON tech.technician_id = sr.technician_id
WHERE m.tech_condition IN ('uszkodzona', 'w_konserwacji')
ORDER BY m.tech_condition, waiting_time DESC NULLS LAST;
