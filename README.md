# UrbanTransit IQ

UrbanTransit IQ is a Big Data and Data Science platform for public-transport analytics. It combines a large generated transport dataset, Spark/HDFS processing, independent Python analytics and a React dashboard.

## What is included

- 2,000,000 ticket records
- 500,000 passenger-count records
- 250,000 delay records
- 100 routes, 500 stops, 250 vehicles and 50,000 passengers
- 12 months of 2025 historical data
- Spark ingestion, cleaning, joins, feature engineering and Spark SQL
- Spark MLlib regression/classification models
- Independent scikit-learn models
- Demand forecasting and occupancy-risk prediction
- Delay prediction, route clustering and passenger segmentation
- Passenger-flow and OD analysis
- Peak demand, persistent overcrowding and underutilization analysis
- Recommendation engine and what-if analysis
- Flask API and React/Vite dashboard
- Data-quality report, cleaning audit and exports
- Automated tests and report-generation scripts

## Windows setup in VS Code

### 1. Open the project

```powershell
cd D:\UrbanTransit-IQ-FINAL
code .
```

Use the folder that contains `run_all.py` if your path is different.

### 2. Create and activate the virtual environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation for the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

### 3. Check Python

```powershell
python --version
where.exe python
```

The first `where.exe python` result should be the project's `.venv` Python.

### 4. Run the complete workflow

```powershell
python run_all.py
```

The script checks the competition dataset before regenerating it. To intentionally regenerate all competition data:

```powershell
python run_all.py --regenerate
```

The workflow runs the Python pipeline every time. If `spark-submit` is configured, it also runs Spark ingestion, Parquet processing, feature engineering, Spark SQL and Spark MLlib. It never creates fake Spark results when Spark is unavailable.

### 5. Run tests

```powershell
pytest -q
```

### 6. Start the backend

Open a new VS Code terminal:

```powershell
cd D:\UrbanTransit-IQ-FINAL
.\.venv\Scripts\Activate.ps1
python backend\app.py
```

The API runs at `http://127.0.0.1:5000`.

### 7. Start the frontend

Open another terminal:

```powershell
cd D:\UrbanTransit-IQ-FINAL\frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, normally `http://localhost:5173`.

The local development account is stored by the backend initialization code. For an evaluator deployment, change the credentials and secret before publishing.

## Spark / HDFS

The project expects Java, Hadoop/HDFS and Apache Spark for the Big Data portion. Confirm that these commands work in the VS Code terminal:

```powershell
java -version
hdfs version
spark-submit --version
```

Then run:

```powershell
python run_all.py
```

The Spark workflow writes cleaned and feature Parquet datasets under `parquet_data/` and model artifacts under `models/spark/`.

## Main folders

- `raw_data/` — generated source data
- `processed_data/` — CSV analytics, metrics and evidence
- `parquet_data/` — Spark output
- `spark_jobs/` — PySpark processing and MLlib
- `spark_sql/` — Spark SQL queries
- `python_pipeline/` — independent Python Data Science workflow
- `dual_pipeline/` — Spark/Python comparison
- `backend/` — Flask API and SQLite metadata/audit storage
- `frontend/` — React dashboard
- `recommendation_engine/` — evidence-based recommendations
- `what_if/` — scenario simulator
- `reports/` — generated project reports
- `tests/` — automated tests
- `documentation/` — project documentation and technical material

## Important generated outputs

After the pipelines run, look for:

- `processed_data/data_quality_report.csv`
- `processed_data/cleaning_audit.csv`
- `processed_data/route_performance.csv`
- `processed_data/peak_demand.csv`
- `processed_data/persistent_overcrowding.csv`
- `processed_data/underutilized_services.csv`
- `processed_data/od_matrix.csv`
- `processed_data/delay_predictions.csv`
- `processed_data/demand_forecast_predictions.csv`
- `processed_data/demand_future_forecast.csv`
- `processed_data/occupancy_risk_predictions.csv`
- `processed_data/spark_model_metrics.csv`
- `processed_data/dual_comparison.csv`
- `processed_data/recommendations.csv`

## Notes

The competition SRS requires deployment, a public repository, a demonstration video, screenshots, evaluator credentials, and a technical blog. Those submission actions must be completed by the team using its own accounts and evidence. The codebase contains preparation/documentation for those deliverables but does not pretend that an external deployment or real video has been completed.
