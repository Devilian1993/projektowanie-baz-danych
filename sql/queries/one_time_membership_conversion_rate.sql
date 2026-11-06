WITH ranked AS (
    SELECT
        m.client_id,
        m.type_id,
        ROW_NUMBER() OVER (
            PARTITION BY m.client_id
            ORDER BY m.purchase_date, m.membership_id
        ) AS purchase_no
    FROM membership m
),
one_time_type AS (
    SELECT type_id
    FROM membership_type
    WHERE name = 'Wejście jednorazowe'
)
SELECT
    ROUND(
        100.0 * COUNT(DISTINCT later.client_id)
        / NULLIF(COUNT(DISTINCT first_purchase.client_id), 0),
        2
    ) AS converted_percentage
FROM ranked first_purchase
LEFT JOIN ranked later
    ON later.client_id = first_purchase.client_id
   AND later.purchase_no > 1
   AND later.type_id NOT IN (
       SELECT type_id FROM one_time_type
   )
WHERE first_purchase.purchase_no = 1
  AND first_purchase.type_id IN (
      SELECT type_id FROM one_time_type
  );