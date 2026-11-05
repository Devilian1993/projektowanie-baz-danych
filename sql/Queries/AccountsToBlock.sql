WITH failed_attempts AS (
    SELECT fl.account_id,
           COUNT(*)             AS attempt_count,
           MIN(fl.attempted_at) AS first_attempt_at,
           MAX(fl.attempted_at) AS last_attempt_at
    FROM failed_login fl
    JOIN user_account ua ON ua.account_id = fl.account_id
    WHERE fl.attempted_at > COALESCE(ua.last_login_at, ua.created_at)
    GROUP BY fl.account_id
    HAVING COUNT(*) >= 5
)
SELECT
    ua.account_id,
    ua.login,
    ua.email,
    CASE
        WHEN a.account_id  IS NOT NULL THEN 'administrator'
        WHEN t.account_id  IS NOT NULL THEN 'trainer'
        WHEN r.account_id  IS NOT NULL THEN 'receptionist'
        WHEN te.account_id IS NOT NULL THEN 'technician'
        WHEN c.account_id  IS NOT NULL THEN 'client'
        ELSE 'unlinked'
    END                                           AS role,
    COALESCE(c.first_name  || ' ' || c.last_name,
             t.first_name  || ' ' || t.last_name,
             r.first_name  || ' ' || r.last_name,
             te.first_name || ' ' || te.last_name,
             a.first_name  || ' ' || a.last_name) AS person_name,
    ua.last_login_at,
    fa.attempt_count,
    fa.first_attempt_at,
    fa.last_attempt_at
FROM failed_attempts fa
JOIN user_account ua ON ua.account_id = fa.account_id
LEFT JOIN client        c  ON c.account_id  = ua.account_id
LEFT JOIN trainer       t  ON t.account_id  = ua.account_id
LEFT JOIN receptionist  r  ON r.account_id  = ua.account_id
LEFT JOIN technician    te ON te.account_id = ua.account_id
LEFT JOIN administrator a  ON a.account_id  = ua.account_id
WHERE ua.is_active          -- only accounts not yet blocked
ORDER BY fa.attempt_count DESC, fa.last_attempt_at DESC;
