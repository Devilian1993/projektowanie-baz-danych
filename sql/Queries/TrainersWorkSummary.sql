WITH params AS (
    SELECT CAST(${Period start, in quotes, e.g. '2026-10-01'} AS DATE) AS date_from,
           CAST(${Period end, in quotes, e.g. '2026-10-31'}   AS DATE) AS date_to
),
pt_stats AS (
    SELECT
        pt.trainer_id,
        COUNT(*) FILTER (WHERE NOT pt.is_cancelled
                           AND pt.ends_at <= CURRENT_TIMESTAMP)  AS completed,
        COUNT(*) FILTER (WHERE NOT pt.is_cancelled
                           AND pt.ends_at >  CURRENT_TIMESTAMP)  AS scheduled,
        COUNT(*) FILTER (WHERE pt.is_cancelled)                  AS cancelled,
        SUM(pt.ends_at - pt.starts_at)
            FILTER (WHERE NOT pt.is_cancelled
                      AND pt.ends_at <= CURRENT_TIMESTAMP)       AS total_time,
        SUM(pt.price)
            FILTER (WHERE NOT pt.is_cancelled
                      AND pt.ends_at <= CURRENT_TIMESTAMP)       AS revenue,
        COUNT(DISTINCT pt.client_id)
            FILTER (WHERE NOT pt.is_cancelled
                      AND pt.ends_at <= CURRENT_TIMESTAMP)       AS client_count
    FROM personal_training pt
    JOIN params p ON pt.starts_at >= p.date_from
                 AND pt.starts_at <  p.date_to + 1
    GROUP BY pt.trainer_id
),
pt_payments AS (   -- settled payments
    SELECT pt.trainer_id, SUM(pay.amount) AS paid_amount
    FROM personal_training pt
    JOIN params           p    ON pt.starts_at >= p.date_from
                              AND pt.starts_at <  p.date_to + 1
    JOIN training_payment tpay ON tpay.training_id = pt.training_id
    JOIN payment          pay  ON pay.payment_id   = tpay.payment_id
    WHERE pay.status = 'oplacona'
    GROUP BY pt.trainer_id
),
enrollments AS (
    SELECT class_id, COUNT(*) AS enrolled_count
    FROM class_enrollment
    GROUP BY class_id
),
gc_stats AS (      -- group classes
    SELECT
        gc.trainer_id,
        COUNT(*) FILTER (WHERE NOT gc.is_cancelled
                           AND gc.starts_at + ct.duration_minutes * INTERVAL '1 minute'
                               <= CURRENT_TIMESTAMP)             AS completed,
        COUNT(*) FILTER (WHERE NOT gc.is_cancelled
                           AND gc.starts_at + ct.duration_minutes * INTERVAL '1 minute'
                               >  CURRENT_TIMESTAMP)             AS scheduled,
        COUNT(*) FILTER (WHERE gc.is_cancelled)                  AS cancelled,
        SUM(ct.duration_minutes * INTERVAL '1 minute')
            FILTER (WHERE NOT gc.is_cancelled
                      AND gc.starts_at + ct.duration_minutes * INTERVAL '1 minute'
                          <= CURRENT_TIMESTAMP)                  AS total_time,
        SUM(COALESCE(e.enrolled_count, 0))
            FILTER (WHERE NOT gc.is_cancelled
                      AND gc.starts_at + ct.duration_minutes * INTERVAL '1 minute'
                          <= CURRENT_TIMESTAMP)                  AS participant_count
    FROM group_class gc
    JOIN params     p  ON gc.starts_at >= p.date_from
                      AND gc.starts_at <  p.date_to + 1
    JOIN class_type ct ON ct.class_type_id = gc.class_type_id
    LEFT JOIN enrollments e ON e.class_id  = gc.class_id
    GROUP BY gc.trainer_id
)
SELECT
    t.trainer_id,
    t.first_name || ' ' || t.last_name                                 AS trainer_name,
    t.training_rate                                                    AS current_rate,

    COALESCE(pts.completed, 0)                                         AS pt_completed,
    COALESCE(pts.scheduled, 0)                                         AS pt_scheduled,
    COALESCE(pts.cancelled, 0)                                         AS pt_cancelled,
    COALESCE(pts.client_count, 0)                                      AS pt_client_count,
    ROUND(COALESCE(EXTRACT(EPOCH FROM pts.total_time), 0) / 3600, 2)   AS pt_hours,
    COALESCE(pts.revenue, 0)                                           AS pt_revenue,
    COALESCE(ptp.paid_amount, 0)                                       AS pt_paid_amount,

    COALESCE(gcs.completed, 0)                                         AS gc_completed,
    COALESCE(gcs.scheduled, 0)                                         AS gc_scheduled,
    COALESCE(gcs.cancelled, 0)                                         AS gc_cancelled,
    ROUND(COALESCE(EXTRACT(EPOCH FROM gcs.total_time), 0) / 3600, 2)   AS gc_hours,
    COALESCE(gcs.participant_count, 0)                                 AS gc_participant_count,
    -- total
    ROUND((COALESCE(EXTRACT(EPOCH FROM pts.total_time), 0)
         + COALESCE(EXTRACT(EPOCH FROM gcs.total_time), 0)) / 3600, 2) AS total_hours
FROM trainer t
LEFT JOIN pt_stats    pts ON pts.trainer_id = t.trainer_id
LEFT JOIN pt_payments ptp ON ptp.trainer_id = t.trainer_id
LEFT JOIN gc_stats    gcs ON gcs.trainer_id = t.trainer_id
ORDER BY total_hours DESC, t.last_name, t.first_name;
