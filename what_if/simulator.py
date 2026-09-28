def simulate(occupancy=0.8, frequency_change=0, capacity_change=0, demand_change=0):
    e = (
        occupancy
        * (1 + demand_change / 100)
        / max((1 + frequency_change / 100) * (1 + capacity_change / 100), 0.01)
    )
    risk = (
        "Critical"
        if e >= 1.1
        else (
            "Overcrowded"
            if e >= 0.95
            else "High" if e >= 0.8 else "Moderate" if e >= 0.6 else "Low"
        )
    )
    return {"estimated_occupancy": e, "risk": risk, "is_estimate": True}
