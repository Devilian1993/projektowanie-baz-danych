WITH params AS (
    SELECT CAST(${Client id, e.g. 15} AS INTEGER) AS client_id
)

SELECT
    training_plan.plan_id,
    training_plan.trainer_id,
    trainer.first_name || ' ' || trainer.last_name AS trainer_name,
    training_plan.name AS plan_name,
    training_plan.goal,
    training_plan.valid_from,
    training_plan.valid_to,
    training_plan.recommendations,
    exercise.name AS exercise_name,
    exercise.description as exercise_description,
    exercise.difficulty_level,
    plan_exercise.set_count,
    plan_exercise.rep_count

FROM params

JOIN training_plan ON training_plan.client_id = params.client_id
JOIN trainer ON trainer.trainer_id = training_plan.trainer_id
LEFT JOIN plan_exercise ON plan_exercise.plan_id = training_plan.plan_id
LEFT JOIN exercise ON exercise.exercise_id = plan_exercise.exercise_id

WHERE training_plan.client_id = params.client_id

ORDER BY training_plan.valid_from DESC, training_plan.plan_id, exercise.name;
