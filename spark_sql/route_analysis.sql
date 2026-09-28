SELECT
    Route_ID,
    SUM(Passenger_Count)            AS Total_Passengers,
    ROUND(AVG(Occupancy_Pct), 2)    AS Avg_Occupancy
FROM passenger_counts
GROUP BY Route_ID
ORDER BY Total_Passengers DESC;