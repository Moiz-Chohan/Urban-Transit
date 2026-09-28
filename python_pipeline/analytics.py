from pathlib import Path

import numpy as np
import pandas as pd

from common import OUT, occupancy, read, save


def _time_features(counts: pd.DataFrame) -> pd.DataFrame:
    x = counts.copy()
    x["service_date"] = pd.to_datetime(x["service_date"], errors="coerce")
    x["day_of_week"] = x["service_date"].dt.dayofweek
    x["is_weekend"] = (x["day_of_week"] >= 5).astype(int)
    # The generated counts table has no event timestamp, so use route/day
    # demand rather than inventing an hour that does not exist in the source.
    return x


def main():
    c = _time_features(occupancy(read("passenger_counts.csv")))
    d = read("delays.csv")
    trips = read("trips.csv")
    route_dim = read("routes.csv")

    if c.empty:
        return

    route = (
        c.groupby("route_id")
        .agg(
            avg_passengers=("passenger_count", "mean"),
            total_passengers=("passenger_count", "sum"),
            avg_occupancy=("occupancy_pct", "mean"),
            max_occupancy=("occupancy_pct", "max"),
            records=("count_id", "count"),
            overcrowded_records=("occupancy_pct", lambda s: int((s >= 0.95).sum())),
            critical_records=("occupancy_pct", lambda s: int((s >= 1.10).sum())),
        )
        .reset_index()
    )

    if not d.empty:
        delay_summary = (
            d.groupby("route_id")
            .agg(
                avg_delay=("delay_minutes", "mean"),
                delay_frequency=("delay_minutes", lambda s: float((s > 5).mean())),
                severe_delay_rate=("delay_minutes", lambda s: float((s > 20).mean())),
            )
            .reset_index()
        )
        route = route.merge(delay_summary, on="route_id", how="left")
    else:
        route["avg_delay"] = 0.0
        route["delay_frequency"] = 0.0
        route["severe_delay_rate"] = 0.0

    route["overcrowding_rate"] = route["overcrowded_records"] / route[
        "records"
    ].replace(0, np.nan)
    under_rates = (
        c.groupby("route_id")["occupancy_pct"]
        .apply(lambda s: float((s < 0.35).mean()))
        .rename("underutilization_rate")
        .reset_index()
    )
    route = route.merge(under_rates, on="route_id", how="left")
    route["reliability"] = (1 - route["avg_delay"].clip(lower=0) / 30).clip(0, 1)
    demand_score = route["avg_passengers"] / max(route["avg_passengers"].max(), 1)
    route["performance_score"] = (
        route["avg_occupancy"].clip(0, 1) * 30
        + route["reliability"] * 30
        + demand_score * 40
    ).round(2)
    route["category"] = np.select(
        [
            route["overcrowding_rate"] >= 0.20,
            route["avg_delay"] >= 10,
            route["underutilization_rate"] >= 0.50,
        ],
        ["Persistent crowding", "Delay concern", "Underutilized"],
        default="Balanced",
    )
    if not route_dim.empty:
        route = route.merge(
            route_dim[["route_id", "route_name", "distance_km"]],
            on="route_id",
            how="left",
        )
    save(
        route.sort_values("performance_score", ascending=False), "route_performance.csv"
    )

    stop_flow = (
        c.groupby("stop_id")
        .agg(
            total_passengers=("passenger_count", "sum"),
            avg_passengers=("passenger_count", "mean"),
            records=("count_id", "count"),
        )
        .reset_index()
        .sort_values("total_passengers", ascending=False)
    )
    save(stop_flow, "stop_flow.csv")

    # Actual demand peaks: identify route/day observations above each route's 90th percentile.
    route_threshold = c.groupby("route_id")["passenger_count"].transform(
        lambda s: s.quantile(0.90)
    )
    peaks = c.loc[c["passenger_count"] >= route_threshold].copy()
    peaks["peak_type"] = np.where(
        peaks["is_weekend"].eq(1), "Weekend peak", "Weekday peak"
    )
    save(
        peaks.groupby(["route_id", "stop_id", "peak_type"], as_index=False)
        .agg(
            peak_records=("count_id", "count"), peak_demand=("passenger_count", "mean")
        )
        .sort_values("peak_demand", ascending=False)
        .head(100),
        "peak_demand.csv",
    )
    save(stop_flow.head(50), "peak_stops.csv")

    # Persistent overcrowding: route/stop combinations where >= 20% of observations are overcrowded.
    persistence = (
        c.groupby(["route_id", "stop_id"])
        .agg(
            records=("count_id", "count"),
            overcrowded_records=("occupancy_pct", lambda s: int((s >= 0.95).sum())),
            avg_occupancy=("occupancy_pct", "mean"),
        )
        .reset_index()
    )
    persistence["overcrowding_rate"] = persistence["overcrowded_records"] / persistence[
        "records"
    ].replace(0, np.nan)
    persistence["persistent_overcrowding"] = persistence["overcrowding_rate"] >= 0.20
    save(
        persistence.sort_values("overcrowding_rate", ascending=False),
        "persistent_overcrowding.csv",
    )

    under = (
        c.groupby(["route_id", "stop_id"])
        .agg(
            records=("count_id", "count"),
            avg_occupancy=("occupancy_pct", "mean"),
            avg_passengers=("passenger_count", "mean"),
        )
        .reset_index()
    )
    under["underutilized"] = under["avg_occupancy"] < 0.35
    save(under.sort_values("avg_occupancy"), "underutilized_services.csv")

    # A journey-level OD approximation using adjacent stop observations from the same trip.
    journey = c.sort_values(["trip_id", "service_date", "count_id"]).copy()
    journey["origin_stop"] = journey["stop_id"]
    journey["destination_stop"] = journey.groupby("trip_id")["stop_id"].shift(-1)
    journey = journey.dropna(subset=["destination_stop"])
    od = journey.groupby(
        ["origin_stop", "destination_stop", "route_id", "is_weekend"], as_index=False
    ).agg(passenger_flow=("passenger_count", "sum"), journeys=("trip_id", "nunique"))
    save(od.sort_values("passenger_flow", ascending=False), "od_matrix.csv")

    anomalies = c[
        (c["passenger_count"] < 0) | (c["passenger_count"] > c["capacity"] * 1.20)
    ].copy()
    anomalies["reason"] = np.select(
        [
            anomalies["passenger_count"] < 0,
            anomalies["passenger_count"] > anomalies["capacity"] * 1.20,
        ],
        ["Negative passenger count", "Extreme capacity violation"],
        default="Review",
    )
    save(anomalies, "anomalies.csv")

    if not trips.empty:
        trips["service_date"] = pd.to_datetime(trips["service_date"], errors="coerce")
        daily = trips.groupby(
            ["route_id", "service_date"], as_index=False
        ).trip_id.nunique()
        daily.rename(columns={"trip_id": "service_frequency"}, inplace=True)
        save(daily, "service_frequency.csv")

    return route


if __name__ == "__main__":
    main()
