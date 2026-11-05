SELECT
    c.client_id,
    c.first_name,
    c.last_name,
    MAX(e.entered_at) AS last_visit,
    CURRENT_DATE - MAX(e.entered_at)::date AS days_since_last_visit

FROM client c

LEFT JOIN entry e
    ON e.account_id = c.account_id
   AND e.result IS TRUE

WHERE EXISTS (
    SELECT 1
    FROM membership m
    JOIN membership_type mt
        ON mt.type_id = m.type_id
    JOIN membership_payment mp
        ON mp.membership_id = m.membership_id
    JOIN payment p
        ON p.payment_id = mp.payment_id

    WHERE m.client_id = c.client_id
      AND m.start_date <= CURRENT_DATE
      AND CURRENT_DATE < m.start_date + mt.validity_period
      AND p.status = 'oplacona'
)

GROUP BY
    c.client_id,
    c.first_name,
    c.last_name

HAVING
    MAX(e.entered_at) IS NULL
    OR MAX(e.entered_at) < CURRENT_TIMESTAMP - INTERVAL '30 days'

ORDER BY
    last_visit NULLS FIRST,
    c.last_name,
    c.first_name;