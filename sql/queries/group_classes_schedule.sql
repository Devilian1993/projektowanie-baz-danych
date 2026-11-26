WITH params AS (
    SELECT CAST(${Day, in quotes, e.g. '2026-11-05'} AS DATE) AS day
)
SELECT
    gc.class_id,
    gc.starts_at::time                                               AS start_time,
    (gc.starts_at + ct.duration_minutes * INTERVAL '1 minute')::time AS end_time,
    ct.name                                                          AS class_name,
    ct.skill_level,
    ct.description,
    r.number                                                         AS room_number,
    r.name                                                           AS room_name,
    t.first_name || ' ' || t.last_name                               AS trainer_name,
    gc.capacity,
    e.enrolled_count,
    CASE WHEN gc.is_cancelled THEN 0
         ELSE gc.capacity - e.enrolled_count
    END                                                              AS free_spots,
    CASE WHEN gc.is_cancelled THEN 'cancelled' ELSE 'scheduled' END  AS status
FROM group_class gc
JOIN params      p  ON gc.starts_at >= p.day
                   AND gc.starts_at <  p.day + 1
JOIN class_type  ct ON ct.class_type_id = gc.class_type_id
JOIN room        r  ON r.room_id        = gc.room_id
JOIN trainer     t  ON t.trainer_id     = gc.trainer_id
CROSS JOIN LATERAL (            -- enrollments counted only for the selected classes
    SELECT COUNT(*) AS enrolled_count
    FROM class_enrollment ce
    WHERE ce.class_id = gc.class_id
) e
ORDER BY gc.starts_at, r.number;

