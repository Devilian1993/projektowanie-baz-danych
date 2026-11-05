SELECT
    s.name AS specialization_name,
    COUNT(ts.trainer_id) AS number_of_trainers
FROM specialization s
    LEFT JOIN trainer_specialization ts ON s.specialization_id = ts.specialization_id
GROUP BY s.name
ORDER BY number_of_trainers DESC;