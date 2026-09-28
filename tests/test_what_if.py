from what_if.simulator import simulate


def test_frequency_reduces_occupancy():
    result = simulate(0.95, 20)
    assert result["estimated_occupancy"] < 0.95


def test_capacity_change_reduces_occupancy():
    base = simulate(0.90, 0)
    larger = simulate(0.90, 0, capacity_change=20)
    assert larger["estimated_occupancy"] < base["estimated_occupancy"]
