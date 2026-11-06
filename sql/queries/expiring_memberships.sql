WITH membership_period AS (
    SELECT m.*,
           mt.name                               AS type_name,
           m.start_date + mt.validity_period - 1 AS end_date,
           CAST(${Number of days ahead} AS INTEGER) AS days_ahead
    FROM membership m
    JOIN membership_type mt ON mt.type_id = m.type_id
)
SELECT
    mp.membership_id,
    c.client_id,
    c.first_name || ' ' || c.last_name           AS client_name,
    c.phone,
    ua.email,
    c.is_student,
    mp.type_name,
    mp.start_date,
    mp.end_date,
    mp.end_date - CURRENT_DATE                   AS days_left
FROM membership_period mp
JOIN client       c  ON c.client_id   = mp.client_id
JOIN user_account ua ON ua.account_id = c.account_id
WHERE mp.end_date BETWEEN CURRENT_DATE AND CURRENT_DATE + mp.days_ahead
  -- membership is paid
  AND EXISTS (
        SELECT 1
        FROM membership_payment mpay
        JOIN payment pay ON pay.payment_id = mpay.payment_id
        WHERE mpay.membership_id = mp.membership_id
          AND pay.status = 'oplacona'
  )
  -- no membership starting after the current one
  AND NOT EXISTS (
        SELECT 1
        FROM membership m2
        WHERE m2.client_id  = mp.client_id
          AND m2.start_date > mp.start_date
  )
  AND mp.end_date > mp.start_date -- Not a 1-time pass
ORDER BY mp.end_date, client_name;

