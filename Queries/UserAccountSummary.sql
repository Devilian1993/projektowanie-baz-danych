WITH counts AS (
    SELECT 'Administrators' as role_name, COUNT(*) AS count
    FROM administrator

    UNION ALL

    SELECT 'Receptionists' as role_name, COUNT(*) AS count
    FROM receptionist

    UNION ALL

    SELECT 'Technicians' as role_name, COUNT(*) AS count
    FROM technician

    UNION ALL

    SELECT 'Trainers' as role_name, COUNT(*) AS count
    FROM trainer

    UNION ALL

    SELECT 'Clients' as role_name, COUNT(*) AS count
    FROM client

    ORDER BY count DESC
)

SELECT role_name, count FROM counts

UNION ALL

SELECT 'Total' as role_name,
       SUM(count)
FROM counts
