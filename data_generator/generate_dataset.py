import argparse
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(__file__))
RAW = os.path.join(ROOT, "raw_data")
rng = np.random.default_rng(42)


def cw(path, n, maker, chunk=100000):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    first = True
    for s in range(0, n, chunk):
        k = min(chunk, n - s)
        maker(s, k).to_csv(
            path,
            index=False,
            mode="w" if first else "a",
            header=first,
        )
        first = False


def generate(size):
    os.makedirs(RAW, exist_ok=True)
    cfg = {
        "demo": (50000, 15000, 10000, 20000),
        "competition": (2000000, 500000, 250000, 500000),
    }[size]
    nt, nc, nd, ntr = cfg

    routes = pd.DataFrame(
        {
            "route_id": [f"R{i:03d}" for i in range(1, 101)],
            "route_name": [f"Route {i:03d}" for i in range(1, 101)],
            "distance_km": rng.uniform(5, 35, 100).round(2),
        }
    )
    stops = pd.DataFrame(
        {
            "stop_id": [f"S{i:04d}" for i in range(1, 501)],
            "stop_name": [f"Stop {i:04d}" for i in range(1, 501)],
            "latitude": rng.uniform(24.75, 25.05, 500).round(6),
            "longitude": rng.uniform(66.85, 67.25, 500).round(6),
        }
    )
    vehicles = pd.DataFrame(
        {
            "vehicle_id": [f"V{i:03d}" for i in range(1, 251)],
            "capacity": rng.integers(35, 81, 250),
        }
    )
    passengers = pd.DataFrame(
        {
            "passenger_id": [f"P{i:05d}" for i in range(1, 50001)],
            "passenger_type": rng.choice(
                ["Regular", "Student", "Worker", "Senior"], 50000
            ),
        }
    )
    route_stop_map = {}
    for r in range(1, 101):
        route_stop_map[f"R{r:03d}"] = [
            f"S{((r - 1) * 5 + k) % 500 + 1:04d}" for k in range(5)
        ]

    rs = pd.DataFrame(
        [
            (f"R{r:03d}", f"S{((r - 1) * 5 + k) % 500 + 1:04d}", k + 1)
            for r in range(1, 101)
            for k in range(5)
        ],
        columns=["route_id", "stop_id", "stop_sequence"],
    )
    cal = pd.DataFrame(
        {
            "service_id": [f"CAL{i:03d}" for i in range(1, 31)],
            "day_type": ["Weekday"] * 20 + ["Weekend"] * 8 + ["Holiday"] * 2,
        }
    )

    for n, d in [
        ("routes", routes),
        ("stops", stops),
        ("vehicles", vehicles),
        ("passengers", passengers),
        ("route_stops", rs),
        ("service_calendar", cal),
    ]:
        d.to_csv(f"{RAW}/{n}.csv", index=False)

    base = pd.Timestamp("2025-01-01")
    trips = pd.DataFrame(
        {
            "trip_id": [f"T{i:07d}" for i in range(1, ntr + 1)],
            "route_id": rng.choice(routes.route_id, ntr),
            "vehicle_id": rng.choice(vehicles.vehicle_id, ntr),
            "service_date": base + pd.to_timedelta(np.arange(ntr) % 365, unit="D"),
            "direction": rng.choice(["Inbound", "Outbound"], ntr),
        }
    )
    trips.to_csv(f"{RAW}/trips.csv", index=False)

    schedules = trips[["trip_id", "route_id", "service_date"]].copy()
    schedules["scheduled_departure"] = pd.to_datetime(
        schedules.service_date
    ) + pd.to_timedelta(rng.integers(5 * 60, 23 * 60, ntr), unit="m")
    schedules["scheduled_arrival"] = schedules.scheduled_departure + pd.to_timedelta(
        rng.integers(15, 90, ntr), unit="m"
    )
    schedules.to_csv(f"{RAW}/schedules.csv", index=False)

    def tickets(s, k):
        ix = rng.integers(0, ntr, k)
        t = trips.iloc[ix].reset_index(drop=True)
        return pd.DataFrame(
            {
                "ticket_id": [f"TK{x:08d}" for x in range(s + 1, s + k + 1)],
                "passenger_id": [f"P{x:05d}" for x in rng.integers(1, 50001, k)],
                "trip_id": t.trip_id,
                "route_id": t.route_id,
                "fare": rng.choice([40, 60, 80, 100, 120], k),
                "status": rng.choice(["Completed", "Cancelled"], k, p=[0.97, 0.03]),
            }
        )

    def counts(s, k):
        ix = rng.integers(0, ntr, k)
        t = trips.iloc[ix].reset_index(drop=True)
        cap = vehicles.set_index("vehicle_id").loc[t.vehicle_id, "capacity"].to_numpy()
        route_numbers = t.route_id.str.extract(r"(\d+)")[0].astype(int).to_numpy()
        stop_sequence = rng.integers(1, 6, k)
        stop_ids = np.array(
            [route_stop_map[r][seq - 1] for r, seq in zip(t.route_id, stop_sequence)]
        )
        start_minutes = (
            schedules.set_index("trip_id")
            .loc[t.trip_id, "scheduled_departure"]
            .dt.hour.to_numpy()
            * 60
        )
        day = pd.to_datetime(t.service_date).dt.dayofyear.to_numpy()
        peak = (
            ((start_minutes // 60 >= 7) & (start_minutes // 60 <= 10))
            | ((start_minutes // 60 >= 16) & (start_minutes // 60 <= 20))
        ).astype(float)
        weekend = (pd.to_datetime(t.service_date).dt.dayofweek.to_numpy() >= 5).astype(
            float
        )
        seasonal = 0.08 * np.sin(2 * np.pi * day / 365.0)
        route_factor = ((route_numbers % 12) / 12.0) * 0.22
        stop_factor = (6 - stop_sequence) * 0.025
        mean_occupancy = (
            0.40 + peak * 0.25 + route_factor + stop_factor - weekend * 0.10 + seasonal
        )
        pc = np.rint(cap * (mean_occupancy + rng.normal(0, 0.10, k))).astype(int)
        pc = np.clip(pc, 0, np.rint(cap * 1.30).astype(int))
        if s == 0:
            pc[0] = -3
            pc[1] = cap[1] + 10
        event_time = pd.to_datetime(
            schedules.set_index("trip_id")
            .loc[t.trip_id, "scheduled_departure"]
            .to_numpy()
        ) + pd.to_timedelta(stop_sequence * 8, unit="m")
        return pd.DataFrame(
            {
                "count_id": [f"PC{x:08d}" for x in range(s + 1, s + k + 1)],
                "trip_id": t.trip_id,
                "route_id": t.route_id,
                "stop_id": stop_ids,
                "stop_sequence": stop_sequence,
                "service_date": t.service_date,
                "event_time": event_time,
                "passenger_count": pc,
                "capacity": cap,
                "boarding": np.clip(
                    np.rint(pc * rng.uniform(0.05, 0.35, k)), 0, None
                ).astype(int),
                "alighting": np.clip(
                    np.rint(pc * rng.uniform(0.02, 0.25, k)), 0, None
                ).astype(int),
            }
        )

    def delays(s, k):
        ix = rng.integers(0, ntr, k)
        t = trips.iloc[ix].reset_index(drop=True)
        route_numbers = t.route_id.str.extract(r"(\d+)")[0].astype(int).to_numpy()
        scheduled = schedules.set_index("trip_id").loc[t.trip_id, "scheduled_departure"]
        hour = scheduled.dt.hour.to_numpy()
        peak = (((hour >= 7) & (hour <= 10)) | ((hour >= 16) & (hour <= 20))).astype(
            float
        )
        route_effect = (route_numbers % 10) * 0.9
        weather_effect = 1.5 * np.sin(
            2 * np.pi * pd.to_datetime(t.service_date).dt.dayofyear.to_numpy() / 365.0
        )
        d = np.rint(
            rng.normal(2.5 + peak * 5 + route_effect + weather_effect, 1.0, k)
        ).astype(int)
        d[0] = 999
        d[1] = -12
        return pd.DataFrame(
            {
                "delay_id": [f"D{x:08d}" for x in range(s + 1, s + k + 1)],
                "trip_id": t.trip_id,
                "route_id": t.route_id,
                "stop_id": rng.choice(stops.stop_id, k),
                "vehicle_id": t.vehicle_id,
                "service_date": t.service_date,
                "scheduled_departure": scheduled.to_numpy(),
                "delay_minutes": d,
            }
        )

    def gps(s, k):
        ix = rng.integers(0, ntr, k)
        t = trips.iloc[ix].reset_index(drop=True)
        return pd.DataFrame(
            {
                "gps_id": [f"G{x:08d}" for x in range(s + 1, s + k + 1)],
                "trip_id": t.trip_id,
                "route_id": t.route_id,
                "latitude": rng.uniform(24.75, 25.05, k),
                "longitude": rng.uniform(66.85, 67.25, k),
                "speed_kmh": rng.uniform(0, 65, k).round(1),
                "event_time": t.service_date.astype(str),
            }
        )

    cw(f"{RAW}/tickets.csv", nt, tickets)
    cw(f"{RAW}/passenger_counts.csv", nc, counts)
    cw(f"{RAW}/delays.csv", nd, delays)
    cw(f"{RAW}/gps_events.csv", max(1000, nc // 5), gps)

    print(
        f"Generated {size}: tickets={nt:,}, passenger movement={nc:,}, "
        f"delays={nd:,}, routes=100, stops=500, vehicles=250, "
        f"passengers=50,000, trips={ntr:,}"
    )


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--size", choices=["demo", "competition"], default="demo")
    generate(a.parse_args().size)
