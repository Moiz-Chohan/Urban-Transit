SELECT
    route_id,
    AVG(passenger_count)                        AS avg_demand,
    AVG(passenger_count / NULLIF(capacity, 0))  AS avg_occupancy,
    COUNT(*)                                    AS movement_records
FROM pc
GROUP BY route_id
ORDER BY avg_demand DESC;