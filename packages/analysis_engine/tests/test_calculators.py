from datetime import datetime

import pytest
from analysis_engine.calculators.timeseries import TimeseriesCalculator
from analysis_engine.schema import FlowDirection, StandardEntry


def test_calculator_flows():
    entries = [
        StandardEntry(
            timestamp=datetime(2026, 6, 1),
            amount=100.0,
            direction=FlowDirection.OUTFLOW,
            category="Food",
        ),
        StandardEntry(
            timestamp=datetime(2026, 6, 2),
            amount=200.0,
            direction=FlowDirection.OUTFLOW,
            category="Shopping",
        ),
        StandardEntry(
            timestamp=datetime(2026, 6, 3),
            amount=1000.0,
            direction=FlowDirection.INFLOW,
            category="Salary",
        ),
    ]
    calc = TimeseriesCalculator(entries)

    total_in = calc.get_total_inflow()
    assert total_in.value == 1000.0

    total_out = calc.get_total_outflow()
    assert total_out.value == 300.0

    net_flow = calc.get_net_flow()
    assert net_flow.value == 700.0  # 1000 - 300


def test_calculator_monthly_summary():
    entries = [
        StandardEntry(
            timestamp=datetime(2026, 5, 1),
            amount=100.0,
            direction=FlowDirection.OUTFLOW,
            category="Food",
        ),
        StandardEntry(
            timestamp=datetime(2026, 6, 1),
            amount=200.0,
            direction=FlowDirection.OUTFLOW,
            category="Food",
        ),
        StandardEntry(
            timestamp=datetime(2026, 6, 2),
            amount=50.0,
            direction=FlowDirection.OUTFLOW,
            category="Transport",
        ),
        StandardEntry(
            timestamp=datetime(2026, 6, 3),
            amount=5000.0,
            direction=FlowDirection.INFLOW,
            category="Salary",
        ),
    ]
    calc = TimeseriesCalculator(entries)
    summary = calc.get_monthly_summary()

    # 应该是 3 条事实 (仅汇总流出: 5月Food, 6月Food, 6月Transport)
    assert len(summary) == 3


def test_calculator_mom_change():
    entries = [
        StandardEntry(
            timestamp=datetime(2026, 5, 1),
            amount=1000.0,
            direction=FlowDirection.OUTFLOW,
            category="Fix",
        ),
        StandardEntry(
            timestamp=datetime(2026, 6, 1),
            amount=1200.0,
            direction=FlowDirection.OUTFLOW,
            category="Fix",
        ),
    ]
    calc = TimeseriesCalculator(entries)
    mom = calc.get_mom_change()

    assert len(mom) == 1
    assert mom[0].change_rate == pytest.approx(0.2)
    assert mom[0].value == 1200.0
