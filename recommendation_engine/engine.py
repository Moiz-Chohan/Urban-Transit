from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "processed_data"


def main():
    source = OUT / "route_performance.csv"
    if not source.exists():
        print(
            "route_performance.csv not found. Run the Python analytics pipeline first."
        )
        return
    performance = pd.read_csv(source)
    rows = []
    for row in performance.itertuples(index=False):
        occ = float(getattr(row, "avg_occupancy", 0))
        delay = float(getattr(row, "avg_delay", 0))
        under = float(getattr(row, "underutilization_rate", 0))
        if occ >= 0.95:
            priority = "Critical"
            recommendation = (
                "Increase service frequency or deploy higher-capacity vehicles."
            )
            basis = "Average occupancy is at or above 95%."
        elif delay >= 10:
            priority = "High"
            recommendation = (
                "Review recurring delay points and adjust departure spacing."
            )
            basis = "Average delay is at least 10 minutes."
        elif under >= 0.50:
            priority = "Medium"
            recommendation = (
                "Review low-demand service frequency against required coverage."
            )
            basis = "At least half of observations are below 35% occupancy."
        else:
            priority = "Low"
            recommendation = "Continue monitoring demand, occupancy and punctuality."
            basis = "No threshold-based operational alert was triggered."
        rows.append(
            {
                "route_id": row.route_id,
                "priority": priority,
                "recommendation": recommendation,
                "evidence": basis,
                "evidence_avg_occupancy": occ,
                "evidence_avg_delay": delay,
                "evidence_underutilization_rate": under,
                "evidence_avg_passengers": float(getattr(row, "avg_passengers", 0)),
            }
        )
    pd.DataFrame(rows).to_csv(OUT / "recommendations.csv", index=False)


if __name__ == "__main__":
    main()
