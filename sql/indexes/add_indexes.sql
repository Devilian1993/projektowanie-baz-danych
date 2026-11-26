CREATE INDEX idx_payment_date_id ON payment (payment_date, payment_id);

CREATE INDEX idx_entry_entered_at_valid ON entry (entered_at) WHERE result = true;

