WITH present_account_data AS (
    SELECT account_id, entered_at
    FROM entry
    WHERE result
      AND exited_at IS NULL
),

users AS (SELECT account_id, 'Administrator' AS role_name, first_name, last_name
          FROM administrator

          UNION ALL

          SELECT account_id, 'Receptionist' AS role_name, first_name, last_name
          FROM receptionist

          UNION ALL

          SELECT account_id, 'Technician' AS role_name, first_name, last_name
          FROM technician

          UNION ALL

          SELECT account_id, 'Trainer' AS role_name, first_name, last_name
          FROM trainer

          UNION ALL

          SELECT account_id, 'Client' AS role_name, first_name, last_name
          FROM client)

SELECT users.role_name,
       users.first_name || ' ' || users.last_name as person_name,
       present_account_data.entered_at
FROM users

JOIN present_account_data ON present_account_data.account_id = users.account_id

ORDER BY users.role_name, present_account_data.entered_at, users.last_name, users.first_name;
