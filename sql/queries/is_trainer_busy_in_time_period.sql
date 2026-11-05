SELECT
    EXISTS (
        SELECT 1
        FROM personal_training pt
        WHERE pt.trainer_id = :target_trainer_id
          AND pt.is_cancelled IS FALSE
          AND pt.starts_at < :end_period
          AND pt.ends_at > :start_period
    )
    OR EXISTS (
        SELECT 1
        FROM group_class gc
        JOIN class_type ct
            ON ct.class_type_id = gc.class_type_id
        WHERE gc.trainer_id = :target_trainer_id
          AND gc.is_cancelled IS FALSE
          AND gc.starts_at < :end_period
          AND gc.starts_at + ct.duration_minutes * INTERVAL '1 minute' > :start_period
    ) AS is_busy;