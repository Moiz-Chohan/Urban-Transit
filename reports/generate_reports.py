from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports"
DATA = ROOT / "processed_data"
OUT.mkdir(exist_ok=True)


def read(n):
    p = DATA / n
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


files = []
for n in [
    "route_performance.csv",
    "data_quality_report.csv",
    "recommendations.csv",
    "dual_comparison.csv",
    "demand_forecast_predictions.csv",
]:
    d = read(n)
    files.append((n, len(d)))
md = [
    "# UrbanTransit IQ — Transport Intelligence Report",
    "",
    "This report is generated from the current processed outputs. It contains no hardcoded analytical conclusions.",
    "",
]
for n, c in files:
    md.append(f"- `{n}`: {c} rows available")
r = read("route_performance.csv")
if not r.empty:
    md += [
        "",
        "## Route performance snapshot",
        "The table below is generated from the processed route-performance output.",
        "",
        r.head(25).to_markdown(index=False),
    ]
q = read("data_quality_report.csv")
if not q.empty:
    md += ["", "## Data quality snapshot", "", q.to_markdown(index=False)]
(OUT / "transport_intelligence_report.md").write_text("\n".join(md), encoding="utf-8")
print("Report written:", OUT / "transport_intelligence_report.md")
