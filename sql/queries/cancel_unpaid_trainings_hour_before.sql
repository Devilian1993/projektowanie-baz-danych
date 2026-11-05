UPDATE personal_training pt
SET is_cancelled = TRUE
WHERE pt.is_cancelled IS FALSE
  AND pt.starts_at BETWEEN CURRENT_TIMESTAMP
                       AND CURRENT_TIMESTAMP + INTERVAL '1 hour'
  AND NOT EXISTS (
      SELECT 1
      FROM training_payment tp
      JOIN payment p ON p.payment_id = tp.payment_id
      WHERE tp.training_id = pt.training_id
        AND p.status = 'oplacona'
  );