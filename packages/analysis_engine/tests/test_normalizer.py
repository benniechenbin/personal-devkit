from datetime import datetime

from analysis_engine.processors.normalizer import DataNormalizer
from analysis_engine.schema import FlowDirection


def test_normalize_basic():
    raw = [
        {
            "date": "2026-06-01",
            "amount": -50.0,
            "category": "Food",
        },  # Negative amount -> OUTFLOW
        {
            "date": "2026-06-02",
            "amount": 18000.0,
            "category": "Salary",
        },  # Positive amount -> OUTFLOW by default if no direction
    ]
    normalizer = DataNormalizer()
    entries = normalizer.normalize(raw)

    assert len(entries) == 2
    assert entries[0].amount == 50.0
    assert entries[0].direction == FlowDirection.OUTFLOW
    assert entries[0].category == "Food"
    assert isinstance(entries[0].timestamp, datetime)

    assert entries[1].amount == 18000.0
    assert entries[1].direction == FlowDirection.OUTFLOW


def test_normalize_chinese_mapping():
    raw = [
        {
            "时间": "2026-06-01",
            "金额": 100.0,
            "类型": "支出",
            "类别": "Shopping",
            "描述": "iPhone",
        },
        {"时间": "2026-06-02", "金额": 5000.0, "类型": "收入", "类别": "Bonus"},
    ]
    # 使用默认的中文映射
    normalizer = DataNormalizer()
    entries = normalizer.normalize(raw)

    assert len(entries) == 2
    assert entries[0].amount == 100.0
    assert entries[0].direction == FlowDirection.OUTFLOW
    assert entries[0].description == "iPhone"

    assert entries[1].amount == 5000.0
    assert entries[1].direction == FlowDirection.INFLOW


def test_normalize_custom_mapping():
    raw = [{"tx_time": "2026-06-01", "tx_val": 200.0, "tx_dir": "in", "tx_cat": "Life"}]
    mapping = {
        "tx_time": "timestamp",
        "tx_val": "amount",
        "tx_dir": "direction",
        "tx_cat": "category",
    }
    normalizer = DataNormalizer(mapping=mapping)
    entries = normalizer.normalize(raw)

    assert len(entries) == 1
    assert entries[0].amount == 200.0
    assert entries[0].direction == FlowDirection.INFLOW
    assert entries[0].category == "Life"
