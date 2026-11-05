SELECT
    payment_id, amount, payment_date, method, purpose, status
FROM payment
WHERE payment_date >= :start_date
  AND payment_date < :end_date
  AND (method ILIKE :method OR :method = '')
  AND (purpose ILIKE :purpose OR :purpose = '')
  AND (status ILIKE :status OR :status = '')
ORDER BY payment_date ASC, payment_id ASC;