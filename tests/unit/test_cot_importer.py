"""Unit tests for ingestion/sources/cot_importer.py — CFTC ZIP CSV parser."""
import io
import csv
import zipfile
import pytest
from ingestion.sources.cot_importer import _parse_cot_zip, GOLD_MARKET_CODE


def _make_zip(rows: list[dict]) -> bytes:
    """Create an in-memory ZIP with an annual.txt CSV containing given rows."""
    buf = io.BytesIO()
    fieldnames = list(rows[0].keys()) if rows else []
    csv_buf = io.StringIO()
    writer = csv.DictWriter(csv_buf, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("annual.txt", csv_buf.getvalue())
    buf.seek(0)
    return buf.read()


def _gold_row(date_str: str, nc_long: int, nc_short: int, **kwargs) -> dict:
    return {
        "CFTC_Contract_Market_Code": GOLD_MARKET_CODE,
        "Report_Date_as_YYYY-MM-DD": date_str,
        "Comm_Positions_Long_All": "10000",
        "Comm_Positions_Short_All": "8000",
        "NonComm_Positions_Long_All": str(nc_long),
        "NonComm_Positions_Short_All": str(nc_short),
        "Open_Interest_All": "200000",
        **kwargs,
    }


class TestParseCotZip:
    def test_empty_zip_returns_empty(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("annual.txt", "")
        result = _parse_cot_zip(buf.getvalue())
        assert result == []

    def test_non_gold_rows_filtered(self):
        rows = [
            {
                "CFTC_Contract_Market_Code": "999999",
                "Report_Date_as_YYYY-MM-DD": "2024-01-02",
                "Comm_Positions_Long_All": "1",
                "Comm_Positions_Short_All": "1",
                "NonComm_Positions_Long_All": "1",
                "NonComm_Positions_Short_All": "1",
                "Open_Interest_All": "1",
            }
        ]
        result = _parse_cot_zip(_make_zip(rows))
        assert result == []

    def test_gold_rows_parsed(self):
        rows = [_gold_row("2024-01-02", nc_long=150000, nc_short=50000)]
        result = _parse_cot_zip(_make_zip(rows))
        assert len(result) == 1
        rec = result[0]
        assert rec["net_noncomm"] == 100000
        assert rec["noncomm_long"] == 150000
        assert rec["noncomm_short"] == 50000
        assert rec["open_interest"] == 200000

    def test_wow_delta_calculated(self):
        rows = [
            _gold_row("2024-01-02", nc_long=100000, nc_short=50000),  # net=50000
            _gold_row("2024-01-09", nc_long=120000, nc_short=50000),  # net=70000, delta=+20000
        ]
        result = _parse_cot_zip(_make_zip(rows))
        assert len(result) == 2
        assert result[1]["net_noncomm_delta_wow"] == 20000

    def test_sorted_ascending_by_date(self):
        rows = [
            _gold_row("2024-03-05", nc_long=80000, nc_short=40000),
            _gold_row("2024-01-02", nc_long=50000, nc_short=30000),
            _gold_row("2024-02-06", nc_long=60000, nc_short=35000),
        ]
        result = _parse_cot_zip(_make_zip(rows))
        dates = [r["report_date"].isoformat() for r in result]
        assert dates == sorted(dates)

    def test_malformed_row_skipped(self):
        rows = [
            _gold_row("2024-01-02", nc_long=100000, nc_short=50000),
            {
                "CFTC_Contract_Market_Code": GOLD_MARKET_CODE,
                "Report_Date_as_YYYY-MM-DD": "not-a-date",
                "Comm_Positions_Long_All": "",
                "Comm_Positions_Short_All": "",
                "NonComm_Positions_Long_All": "",
                "NonComm_Positions_Short_All": "",
                "Open_Interest_All": "",
            },
        ]
        result = _parse_cot_zip(_make_zip(rows))
        assert len(result) == 1  # malformed row skipped
