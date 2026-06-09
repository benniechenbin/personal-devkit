from datetime import datetime

from analysis_engine.detectors.outliers import OutlierDetector
from analysis_engine.schema import FlowDirection, StandardEntry


def test_outlier_detection():
    # 模拟数据：餐饮一般 50-100，突然来个 2000 的
    entries = [
        StandardEntry(
            timestamp=datetime(2026, 6, 1),
            amount=50.0,
            direction=FlowDirection.OUTFLOW,
            category="Food",
        ),
        StandardEntry(
            timestamp=datetime(2026, 6, 2),
            amount=60.0,
            direction=FlowDirection.OUTFLOW,
            category="Food",
        ),
        StandardEntry(
            timestamp=datetime(2026, 6, 3),
            amount=70.0,
            direction=FlowDirection.OUTFLOW,
            category="Food",
        ),
        StandardEntry(
            timestamp=datetime(2026, 6, 4),
            amount=2000.0,
            direction=FlowDirection.OUTFLOW,
            category="Food",
            description="Fancy Dinner",
        ),
        # 即使有巨大的收入，也不应该误报（我们只检测 OUTFLOW）
        StandardEntry(
            timestamp=datetime(2026, 6, 5),
            amount=50000.0,
            direction=FlowDirection.INFLOW,
            category="Bonus",
        ),
    ]

    detector = OutlierDetector(entries, threshold=2.0)
    anomalies = detector.detect_category_outliers()

    assert len(anomalies) == 1
    assert "2000" in anomalies[0].message
    assert anomalies[0].related_entries[0].description == "Fancy Dinner"


def test_outlier_small_ignore():
    # 模拟数据：虽然超过均值很多，但绝对值很小 (10元 vs 2元均值)，不应报警
    entries = [
        StandardEntry(
            timestamp=datetime(2026, 6, 1),
            amount=1.0,
            direction=FlowDirection.OUTFLOW,
            category="Small",
        ),
        StandardEntry(
            timestamp=datetime(2026, 6, 2),
            amount=10.0,
            direction=FlowDirection.OUTFLOW,
            category="Small",
        ),
    ]
    detector = OutlierDetector(entries, threshold=2.0)
    anomalies = detector.detect_category_outliers()

    assert len(anomalies) == 0
