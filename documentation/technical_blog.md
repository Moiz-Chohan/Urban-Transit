# Building UrbanTransit IQ: A Big Data and Data Science Approach to Public Transport Intelligence

## Introduction

Urban public transport systems generate large amounts of operational information. Passenger movements, tickets, route assignments, stop activity, vehicle capacity, schedules, GPS events and delays are produced continuously. The challenge is not simply storing these records. Transport operators need to turn them into decisions: where demand is highest, which services are overcrowded, where capacity is being wasted, which routes experience recurring delays, how passenger demand may change, and which operational changes deserve attention.

UrbanTransit IQ was designed as a practical analytics platform for this problem. The project combines a large synthetic transport dataset with Hadoop/HDFS, Apache Spark, Spark SQL, Spark MLlib, an independent Python Data Science workflow and a web dashboard. The architecture deliberately separates large-scale processing from independent modelling so that results can be compared rather than relying on a single implementation.

## The transport data problem

A realistic transport dataset must contain more than a few demonstration rows. UrbanTransit IQ therefore uses connected tables for passengers, tickets, routes, stops, route-stop relationships, trips, schedules, vehicles, passenger counts, delays, GPS events and service calendars. The competition dataset contains at least two million ticket records, five hundred thousand passenger-count records, two hundred fifty thousand delay records, one hundred routes, five hundred stops, two hundred fifty vehicles and fifty thousand passengers over twelve months.

The generator intentionally includes operational problems such as negative passenger counts, capacity violations, cancelled tickets, negative or extreme delays and different levels of passenger demand. These conditions make data quality analysis meaningful. A transport analytics system should not silently assume that every source record is correct.

## Data generation and integration

The data-generation scripts are kept inside the repository because reproducibility is important. The generator uses a fixed random seed so the same configuration can be recreated for testing. The source tables use common identifiers such as route ID, trip ID, stop ID and vehicle ID. This allows the Spark workflow to join fact records with transport dimensions.

The processing layer standardizes column names, removes duplicate primary keys where appropriate, filters invalid passenger counts and capacities, calculates occupancy and derives day-type features. The cleaning stage also creates an audit-oriented output describing the validation rules. This gives evaluators a clearer view of what was detected and what the processing pipeline did with those records.

## Hadoop and HDFS

HDFS is intended to provide distributed storage for the large source data. The project keeps the raw data separate from processed data so that the original inputs remain available for audit and regeneration. A competition environment can load the raw CSV tables into HDFS and then point Spark at the distributed files.

The architecture does not require the web application to read millions of raw rows for every page request. Instead, Spark prepares analytical datasets and Parquet outputs. The dashboard reads compact analytical results through the Flask API. This separation is important because repeatedly scanning the full ticket dataset during a user interaction would be unnecessary and slow.

## Apache Spark processing

Apache Spark is the main Big Data processing engine. The Spark workflow reads the connected transport tables, normalizes schemas, performs joins, cleans passenger-count data and calculates occupancy. Data is written as Parquet and partitioned by route where useful. Spark SQL is also used for route-level aggregation so that SQL-based evidence is present in the project rather than only DataFrame transformations.

Feature engineering creates variables such as occupancy percentage, crowding level, previous route demand, rolling route demand, daily route demand and demand pressure. These features support both descriptive analytics and machine-learning tasks.

## Passenger flow and origin-destination analysis

Passenger flow analysis identifies stops with high total and average passenger movement. Origin-destination analysis is constructed from trip-linked stop observations and stores origin, destination, route, day type, passenger flow and journey counts. This allows the dashboard and reports to discuss movement patterns instead of showing only route totals.

The source data does not contain a complete passenger journey timestamp sequence for every passenger. Therefore, the project treats the OD result as an analytical approximation based on the available trip and stop records rather than claiming it is a perfect ticket-to-ticket journey reconstruction. This limitation should be documented during the competition demonstration.

## Peak demand and overcrowding

Peak detection is based on actual passenger demand. Route-level demand distributions are used to identify observations at or above the route's high-demand threshold. Peak results can then be summarized by route, stop and day type.

Overcrowding is measured using occupancy, calculated as passenger count divided by vehicle capacity. Services at or above ninety-five percent occupancy are flagged as overcrowded, while very high occupancy is classified as critical. Persistent overcrowding goes beyond one unusual observation. The project calculates the proportion of overcrowded observations for route-stop combinations and flags combinations where the overcrowding rate is at least twenty percent.

Underutilization is treated similarly. Services with average occupancy below thirty-five percent are identified so that operators can compare excess capacity with areas of excess demand. These thresholds are configurable business rules rather than universal transport laws and should be interpreted in the context of the competition dataset.

## Route performance

Route performance combines passenger demand, occupancy and delay information. The project calculates average passengers, total passengers, average and maximum occupancy, overcrowding rate, delay frequency, severe-delay rate and a bounded reliability measure. A performance score is used for sorting the dashboard, while the underlying metrics remain visible so that the score is not treated as a hidden decision.

The recommendation engine uses these observable metrics. For example, a route with very high occupancy can receive a recommendation to consider higher service frequency or higher-capacity vehicles. A route with recurring delays can be flagged for schedule and departure-spacing review. A low-utilization route can be reviewed for frequency versus coverage requirements.

## Delay analytics and prediction

Delay analysis separates descriptive delay statistics from predictive modelling. The descriptive layer calculates average delay, delay frequency and severe-delay frequency by route. The predictive model classifies delay severity using historical route and stop context, calendar information and lagged historical route delay. The current delay value itself is not used as a predictor of its own severity, avoiding the direct target leakage present in a simplistic one-variable model.

The Python model uses chronological validation so later records are not used to train predictions for earlier periods. Model metrics include accuracy, precision, recall and macro F1. The saved model and prediction output provide evidence that the result came from a reproducible pipeline.

## Demand forecasting

Demand forecasting uses daily network passenger totals. The model includes day-of-week, month, trend, one-day lag, seven-day lag and a rolling seven-day demand feature. A chronological train/test split is used. A previous-day (lag-one) baseline is also calculated so the model can be compared with a simple documented forecasting method.

After evaluation, the model produces a configurable future horizon. The current project uses fourteen future days by default. The dashboard displays recent historical observations together with the forecast period. This structure can later be extended to route-level and stop-level forecasts without redesigning the complete application.

## Occupancy prediction

Occupancy risk is formulated as a classification task. A record is labelled as high risk when occupancy reaches ninety-five percent. The Python model uses capacity, boarding, alighting, route and stop identifiers, calendar features and lagged historical route occupancy. The lagged feature is calculated from earlier observations so the current passenger count is not directly supplied to the classifier.

This model is intentionally independent of Spark. It uses scikit-learn and a chronological split. The result includes accuracy, precision, recall and F1 and saves both the model and test predictions.

## Spark MLlib and independent Python modelling

The project evaluates three Spark MLlib regression algorithms: linear regression, random forest regression and gradient-boosted tree regression. An additional Spark random-forest classifier is used for occupancy-risk comparison. Model metrics and saved Spark model artifacts provide evidence for the modelling requirement.

The independent Python pipeline uses scikit-learn models. The two workflows are not supposed to be identical implementations. Their agreement and disagreement are measured on unseen occupancy cases when both pipelines have produced predictions. This is more meaningful than copying a ground-truth label into a field called a Spark prediction.

## Route clustering and passenger segmentation

Route clustering groups routes using demand, occupancy, delay and performance variables. Passenger segmentation groups passengers using observed ticket usage, number of trips and average fare. These unsupervised analyses can help operators identify groups of routes or passengers with similar operational characteristics.

Clustering results should be treated as descriptive groupings rather than automatically assigning policy decisions. The recommendation layer remains threshold- and evidence-based so that the reasons for an operational suggestion remain visible.

## Dashboard and application architecture

The web application uses React and Vite for the frontend and Flask for the backend. The frontend includes dashboard, route, passenger flow, delay, occupancy, recommendation, forecast, data-quality, model-comparison, network-map and what-if views. Search and sorting are provided for route results, and CSV export endpoints are available for analytical outputs.

The backend reads prepared analytical files rather than recomputing the full dataset on every request. SQLite is used for application metadata and audit logging. This is appropriate for a competition prototype and can later be replaced by PostgreSQL or another production database if the deployment environment requires it.

## What-if analysis

The what-if module estimates occupancy after changes in demand, frequency and vehicle capacity. The calculation is explicitly presented as an estimate rather than a guaranteed operational prediction. This distinction is important because a scenario simulator does not know every external variable affecting a real transport system.

## Testing and reproducibility

Testing includes project structure checks and scenario tests. The complete workflow also separates data generation, data-quality auditing, Python modelling, Spark processing, recommendations and report generation into explicit steps. This makes troubleshooting easier for a beginner developer because each stage can be executed independently.

The README provides Windows and VS Code commands for environment setup, Python dependencies, Spark checks, backend startup, frontend startup and test execution. The project also removes cached Python and frontend dependencies from the submission package so the recipient can install dependencies for the target operating system instead of receiving incompatible local binaries.

## Security and limitations

The Flask application uses session-based login and stores password hashes rather than plain-text passwords. A deployment should replace the development secret and local credentials before publishing. CORS and database configuration should also be tightened for production use.

The dataset is synthetic, so its results should not be interpreted as real-world measurements. The geographic coordinates are generated data and the OD reconstruction is an approximation. Forecasts and model metrics describe the generated dataset and may not generalize to a real city. These limitations are part of the project documentation rather than hidden from the evaluator.

## Conclusion

UrbanTransit IQ demonstrates how a transport analytics problem can be organized into a reproducible Big Data and Data Science workflow. The key design principle is separation: raw data remains auditable, Spark performs large-scale processing, Python provides an independent modelling path, and the dashboard consumes prepared analytical outputs. This makes the system easier to test, explain and extend.

The remaining competition deliverables are operational rather than purely code-based. The team must configure its final Hadoop/Spark environment, verify runtime metrics, deploy the application, publish the repository, record the required demonstration video, capture screenshots and complete the final report and contribution records. Those steps should be performed and verified by the team before submission.
