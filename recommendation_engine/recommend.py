from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
c = pd.read_csv(ROOT / "raw_data/passenger_counts.csv")
g = (
    c.groupby("Route_ID")
    .agg(
        avg_occupancy=("Occupancy_Pct", "mean"),
        total_passengers=("Passenger_Count", "sum"),
        trips=("Trip_ID", "nunique"),
    )
    .reset_index()
)


def rec(x):
    if x.avg_occupancy >= 100:
        return ("Increase peak service or assign higher-capacity vehicles", "Critical")
    if x.avg_occupancy >= 90:
        return ("Review peak frequency and vehicle capacity", "High")
    if x.avg_occupancy < 30:
        return ("Review frequency and schedule alignment", "Medium")
    return ("Continue monitoring route performance", "Low")


g[["Recommendation", "Priority"]] = g.apply(lambda x: pd.Series(rec(x)), axis=1)
(ROOT / "reports").mkdir(exist_ok=True)
g.to_csv(ROOT / "reports/route_recommendations.csv", index=False)
