from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw_data"
OUT = ROOT / "processed_data"


def main():
    OUT.mkdir(exist_ok=True)
    counts = pd.read_csv(RAW / "passenger_counts.csv")
    delays = pd.read_csv(RAW / "delays.csv")
    tickets = pd.read_csv(RAW / "tickets.csv")
    trips = pd.read_csv(RAW / "trips.csv")
    issues = []

    def add(table, rule, count, severity="warning"):
        issues.append(
            {"table": table, "rule": rule, "count": int(count), "severity": severity}
        )

    add(
        "passenger_counts",
        "negative_passenger_count",
        (counts.passenger_count < 0).sum(),
        "error",
    )
    add(
        "passenger_counts",
        "capacity_violation",
        (counts.passenger_count > counts.capacity).sum(),
        "warning",
    )
    add("passenger_counts", "invalid_capacity", (counts.capacity <= 0).sum(), "error")
    add("passenger_counts", "missing_trip_id", counts.trip_id.isna().sum(), "error")
    add(
        "passenger_counts",
        "duplicate_count_id",
        counts.count_id.duplicated().sum(),
        "error",
    )
    add("delays", "negative_delay", (delays.delay_minutes < 0).sum(), "warning")
    add(
        "delays",
        "extreme_delay_over_120m",
        (delays.delay_minutes.abs() > 120).sum(),
        "warning",
    )
    add("delays", "duplicate_delay_id", delays.delay_id.duplicated().sum(), "error")
    add("tickets", "duplicate_ticket_id", tickets.ticket_id.duplicated().sum(), "error")
    add("tickets", "cancelled_tickets", (tickets.status == "Cancelled").sum(), "info")
    add("trips", "duplicate_trip_id", trips.trip_id.duplicated().sum(), "error")
    add("trips", "missing_route_id", trips.route_id.isna().sum(), "error")

    report = pd.DataFrame(issues)
    report.to_csv(OUT / "data_quality_report.csv", index=False)

    audit = pd.DataFrame(
        [
            {
                "table": "passenger_counts",
                "issue": "negative_passenger_count",
                "rule": "Remove records where passenger_count < 0",
                "corrected_value": "Record removed from Spark clean table",
                "final_status": "handled by Spark cleaning",
            },
            {
                "table": "passenger_counts",
                "issue": "capacity_violation",
                "rule": "Flag passenger_count > capacity for review",
                "corrected_value": "Retained for audit; extreme rows are flagged",
                "final_status": "flagged",
            },
            {
                "table": "delays",
                "issue": "extreme_delay_over_120m",
                "rule": "Flag absolute delay > 120 minutes",
                "corrected_value": "Retained for investigation",
                "final_status": "flagged",
            },
            {
                "table": "tickets",
                "issue": "duplicate_ticket_id",
                "rule": "Deduplicate by ticket_id",
                "corrected_value": "Spark clean stage removes duplicate keys where applicable",
                "final_status": "handled by cleaning",
            },
        ]
    )
    audit.to_csv(OUT / "cleaning_audit.csv", index=False)
    print(report.to_string(index=False))


if __name__ == "__main__":
    main()
