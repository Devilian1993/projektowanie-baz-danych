SELECT
    e.name AS exercise_name, e.description
FROM exercise e
    LEFT JOIN required_equipment re ON e.exercise_id = re.exercise_id
    LEFT JOIN equipment_category ec ON re.category_id = ec.category_id
WHERE (e.difficulty_level ILIKE :exercise_difficulty OR :exercise_difficulty = '')
    AND (ec.name ILIKE :equipment_name OR :equipment_name = '')
ORDER BY e.name ASC;
