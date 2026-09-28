from pathlib import Path

import joblib
import pandas as pd
from sklearn.cluster import KMeans

from common import OUT, save

ROOT = Path(__file__).resolve().parents[1]


def main():
    x = pd.read_csv(Path(OUT) / "route_performance.csv")
    cols = ["avg_passengers", "avg_occupancy", "avg_delay", "performance_score"]
    z = x[cols].fillna(0)
    k = KMeans(n_clusters=min(5, max(2, len(x))), random_state=42, n_init=10)
    x["cluster"] = k.fit_predict(z)
    save(x, "route_clusters.csv")
    joblib.dump(k, ROOT / "models" / "route_clustering_model.joblib")


if __name__ == "__main__":
    main()
