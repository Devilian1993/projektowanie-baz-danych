SELECT DISTINCT ON (ct.skill_level)
    ct.skill_level,
    ct.name AS class_type_name,
    COUNT(ce.client_id) AS total_enrollments
FROM class_type ct
JOIN group_class gc
    ON gc.class_type_id = ct.class_type_id
LEFT JOIN class_enrollment ce
    ON ce.class_id = gc.class_id
WHERE gc.is_cancelled IS FALSE
GROUP BY ct.skill_level, ct.class_type_id, ct.name
ORDER BY
    ct.skill_level,
    COUNT(ce.client_id) DESC,
    ct.class_type_id;