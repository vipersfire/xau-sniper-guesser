"""Unit tests for ota/validator.py"""
import json
import tempfile
import os
import pytest
from pathlib import Path
from ota.validator import verify_params_file, verify_strategy_module


VALID_PARAMS = {
    "confidence_threshold": 0.65,
    "position_sizing": {"base_risk_pct": 1.0, "min_lot": 0.01, "max_lot": 1.0},
    "circuit_breaker": {"gold_30min_move_pct": 1.5},
}


def _write_json(data: dict) -> Path:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    )
    json.dump(data, f)
    f.close()
    return Path(f.name)


def _write_py(code: str) -> Path:
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    )
    f.write(code)
    f.close()
    return Path(f.name)


class TestVerifyParamsFile:
    def test_valid_params_pass(self):
        path = _write_json(VALID_PARAMS)
        try:
            ok, msg = verify_params_file(path)
            assert ok
            assert msg == "OK"
        finally:
            os.unlink(path)

    def test_invalid_json_fails(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        f.write("{invalid json}")
        f.close()
        try:
            ok, msg = verify_params_file(Path(f.name))
            assert not ok
            assert "JSON" in msg or "json" in msg.lower()
        finally:
            os.unlink(f.name)

    def test_missing_required_key_fails(self):
        data = {**VALID_PARAMS}
        del data["confidence_threshold"]
        path = _write_json(data)
        try:
            ok, msg = verify_params_file(path)
            assert not ok
            assert "confidence_threshold" in msg
        finally:
            os.unlink(path)

    def test_confidence_out_of_range_fails(self):
        data = {**VALID_PARAMS, "confidence_threshold": 1.5}
        path = _write_json(data)
        try:
            ok, msg = verify_params_file(path)
            assert not ok
        finally:
            os.unlink(path)

    def test_confidence_zero_fails(self):
        data = {**VALID_PARAMS, "confidence_threshold": 0.0}
        path = _write_json(data)
        try:
            ok, msg = verify_params_file(path)
            assert not ok
        finally:
            os.unlink(path)

    def test_file_not_found_fails(self):
        ok, msg = verify_params_file(Path("/nonexistent/path.json"))
        assert not ok


class TestVerifyStrategyModule:
    def test_valid_python_passes(self):
        path = _write_py("def entry(features):\n    return None\n")
        try:
            ok, msg = verify_strategy_module(path)
            assert ok
        finally:
            os.unlink(path)

    def test_syntax_error_fails(self):
        path = _write_py("def broken(\n    return None\n")
        try:
            ok, msg = verify_strategy_module(path)
            assert not ok
            assert "yntax" in msg
        finally:
            os.unlink(path)

    def test_empty_file_passes(self):
        path = _write_py("")
        try:
            ok, msg = verify_strategy_module(path)
            assert ok
        finally:
            os.unlink(path)
