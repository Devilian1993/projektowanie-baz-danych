CREATE INDEX IF NOT EXISTS idx_group_class_starts_at
    ON group_class (starts_at);

CREATE INDEX IF NOT EXISTS idx_personal_training_starts_at
    ON personal_training (starts_at);

CREATE INDEX IF NOT EXISTS idx_service_request_open
    ON service_request (machine_id, reported_at)
    WHERE end_date IS NULL;

CREATE INDEX IF NOT EXISTS idx_membership_payment_membership
    ON membership_payment (membership_id);

CREATE INDEX IF NOT EXISTS idx_membership_client_start
    ON membership (client_id, start_date);

CREATE INDEX IF NOT EXISTS idx_class_enrollment_class
    ON class_enrollment (class_id);

ANALYZE;