WITH stats AS (SELECT mm.manufacturer,
                      mm.model,
                      ROUND(COUNT(sr.request_id) * 100.0 / NULLIF(COUNT(DISTINCT m.machine_id), 0), 2) AS percentage,
                      COUNT(DISTINCT m.machine_id) AS total_machines,
                      COUNT(sr.request_id)         AS total_breakdowns
               FROM machine_model mm
                        LEFT JOIN machine m ON mm.model_id = m.model_id
                        LEFT JOIN service_request sr ON m.machine_id = sr.machine_id
               GROUP BY mm.model_id, mm.manufacturer, mm.model
            )
SELECT
    manufacturer,
    model,
    percentage || '%' AS breakdown_percentage,
    total_breakdowns,
    total_machines
FROM stats
ORDER BY percentage DESC, total_breakdowns DESC;