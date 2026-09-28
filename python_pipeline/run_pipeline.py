import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    ("network analytics", "python_pipeline/analytics.py"),
    ("route clustering", "python_pipeline/route_clustering.py"),
    ("occupancy risk", "python_pipeline/occupancy_risk.py"),
    ("passenger segmentation", "python_pipeline/passenger_segmentation.py"),
    ("demand forecasting", "python_pipeline/demand_forecasting.py"),
    ("delay prediction", "python_pipeline/delay_model.py"),
]


def main():
    for label, script in STEPS:
        print(f"\n>>> Python {label}", flush=True)
        subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, check=True)
    print("\nPython analytics and data-science pipeline completed.", flush=True)


if __name__ == "__main__":
    main()
