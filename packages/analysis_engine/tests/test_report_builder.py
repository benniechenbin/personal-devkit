from analysis_engine.synthesis.report_builder import ReportBuilder


def test_full_report_flow():
    raw_data = [
        {
            "date": "2026-05-01",
            "amount": 1000.0,
            "direction": "out",
            "category": "Rent",
        },
        {
            "date": "2026-06-01",
            "amount": 1000.0,
            "direction": "out",
            "category": "Rent",
        },
        {
            "date": "2026-06-02",
            "amount": 2000.0,
            "direction": "out",
            "category": "Shopping",
            "description": "New PC",
        },
        {
            "date": "2026-06-05",
            "amount": 10000.0,
            "direction": "in",
            "category": "Salary",
        },
    ]

    builder = ReportBuilder()
    report = builder.build_report(raw_data)

    assert report.raw_entry_count == 4
    assert len(report.metrics) > 0

    assert "**总流入**: 10000.0" in report.summary_text
    assert "**总流出**: 4000.0" in report.summary_text
    assert "**净流量**: 6000.0" in report.summary_text

    raw_data_2 = [
        {"date": "2026-06-01", "amount": 50.0, "direction": "out", "category": "Food"},
        {"date": "2026-06-02", "amount": 50.0, "direction": "out", "category": "Food"},
        {
            "date": "2026-06-03",
            "amount": 1200.0,
            "direction": "out",
            "category": "Food",
            "description": "Caviar",
        },
    ]
    report_2 = builder.build_report(raw_data_2)
    assert len(report_2.anomalies) == 1
    assert "Food" in report_2.summary_text
    assert "1200" in report_2.summary_text

    print(report_2.summary_text)


if __name__ == "__main__":
    test_full_report_flow()
