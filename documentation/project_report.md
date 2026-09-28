# UrbanTransit IQ Project Report

## 1. Problem Definition

Urban public transport generates large and connected datasets. Operators need to understand demand, passenger movement, capacity pressure, delays, route performance and future operating conditions. UrbanTransit IQ provides a web-based analytical platform that processes generated transport data and turns it into operational indicators and recommendations.

## 2. Proposed Solution

The solution combines data generation, data-quality validation, HDFS/Spark processing, Spark SQL, feature engineering, MLlib modelling, an independent Python workflow, a Flask API, SQLite metadata storage and a React dashboard. The application separates large-scale data preparation from interactive dashboard requests.

## 3. Dataset and Data Model

The competition dataset contains at least 2,000,000 tickets, 500,000 passenger-count records, 250,000 delay records, 100 routes, 500 stops, 250 vehicles, 50,000 passengers and twelve months of historical data. Connected tables include passengers, tickets, routes, stops, route_stops, trips, schedules, vehicles, passenger_counts, delays, GPS events and service_calendar.

Primary identifiers include passenger_id, ticket_id, route_id, stop_id, trip_id, vehicle_id, count_id and delay_id. Foreign-key relationships connect passenger activity to trips and routes and connect operational records to stops and vehicles.

## 4. Data Quality

The quality layer checks negative passenger values, invalid capacities, capacity violations, missing trip identifiers, duplicate IDs, negative delays, extreme delays, cancelled tickets and duplicate trip identifiers. A cleaning audit records the validation rule and the treatment applied by the processing workflow.

## 5. Big Data Architecture

Raw CSV data is stored separately from processed output. Hadoop/HDFS is used as the distributed storage layer in the target execution environment. Spark reads the raw tables, standardizes schemas, performs joins and transformations, and writes Parquet output. Route partitioning supports selective analytical reads.

## 6. Feature Engineering

Core features include occupancy percentage, crowding level, weekend indicator, previous route demand, rolling route demand, daily route demand, utilization and demand-pressure class. These features support descriptive analytics and machine-learning tasks.

## 7. Passenger Flow and OD

Stop-level passenger totals identify high-movement locations. The OD dataset is built from trip-linked stop observations and contains origin, destination, route, day type, passenger flow and journey counts. Because the generated source does not provide a complete individual journey sequence, OD results are treated as an approximation based on available trip-stop observations.

## 8. Peak, Overcrowding and Underutilization

Peak demand is identified using high-percentile passenger demand by route. Overcrowding begins at 95% occupancy, with 110% used for the critical category. Persistent overcrowding is calculated using the share of observations meeting the overcrowding threshold. Underutilization is identified below 35% occupancy.

## 9. Route and Delay Analytics

Route performance combines demand, occupancy, overcrowding, delay frequency, severe-delay frequency and reliability. Delay analysis summarizes route-level delay behaviour. Delay severity prediction uses route, stop, vehicle and calendar features plus lagged historical route delay and is evaluated chronologically.

## 10. Forecasting and Occupancy Prediction

Demand forecasting uses lagged and calendar features and compares the model with a lag-seven baseline. A future horizon is generated after model training. Occupancy-risk prediction is a binary classification problem based on 95% occupancy. The Python model uses lagged historical occupancy and operational features without supplying the current passenger count as a predictor.

## 11. Spark MLlib

Three Spark regression algorithms are evaluated: linear regression, random forest regression and gradient-boosted tree regression. Spark also evaluates a random-forest occupancy classifier. The project records model metrics and saves Spark model artifacts.

## 12. Independent Python Pipeline

The Python workflow uses pandas and scikit-learn. It produces route analytics, clustering, segmentation, demand forecasting, occupancy-risk prediction and delay prediction. It is separate from the Spark MLlib implementation.

## 13. Dual-Pipeline Comparison

Spark and Python occupancy predictions are merged by count_id and compared on common unseen test cases. Agreement and disagreement are reported. The system does not copy ground-truth labels into the Spark result field.

## 14. Recommendation Engine

Recommendations are generated from visible evidence. High occupancy leads to capacity/frequency review, recurring delay leads to schedule review, and persistent underutilization leads to frequency-versus-coverage review. The output includes priority and evidence fields.

## 15. Web Application

The React frontend contains network overview, route performance, passenger flow, delays, occupancy, recommendations, forecasting, data quality, model comparison, network map and what-if views. The Flask API exposes analytical results and CSV export endpoints. SQLite stores user metadata and audit actions.

## 16. What-If Analysis

The simulator estimates the effect of demand, frequency and capacity changes on occupancy. Results are explicitly marked as estimates and are intended for scenario exploration rather than guaranteed operational forecasts.

## 17. Testing

The repository contains automated tests for core project structure and the what-if simulator. The final team verification should also run the full pipeline, Spark jobs, frontend build, API endpoints and model outputs on the target Windows environment.

## 18. Security and Privacy

Passwords are stored as SHA-256 hashes in the local SQLite database and application actions are recorded in an audit table. Production deployment should replace the development secret, credentials and local configuration and should use stronger password-management and deployment controls.

## 19. Limitations

The transport dataset is synthetic. Generated coordinates are not real operational measurements. OD results are based on available trip-stop information. Forecasts and model metrics describe the generated dataset. External live ticketing, GPS hardware and traffic-control integrations are outside the mandatory project scope.

## 20. Future Enhancement

Future versions can add real-time streaming, stronger journey reconstruction, route-level time-series models, weather and event data, production PostgreSQL storage, role-based permissions, automated Spark monitoring and cloud deployment.

## 21. Final Verification

Before competition submission, the team should verify Spark/HDFS execution, record actual model metrics, confirm that dashboards consume generated results, deploy the application, create screenshots, record the mandatory demonstration video, publish the technical blog, complete the contribution record and review AI_USAGE.md.
