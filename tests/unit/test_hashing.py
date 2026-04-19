"""Unit tests for utils/hashing.py"""
import tempfile
import os
import pytest
from utils.hashing import sha256_file, sha256_bytes, sha256_str


class TestSHA256Str:
    def test_known_hash(self):
        # sha256("hello") is well-known
        result = sha256_str("hello")
        assert result == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    def test_empty_string(self):
        result = sha256_str("")
        assert len(result) == 64  # 256 bits = 64 hex chars

    def test_different_inputs_differ(self):
        assert sha256_str("abc") != sha256_str("abd")

    def test_same_input_same_hash(self):
        assert sha256_str("test") == sha256_str("test")


class TestSHA256Bytes:
    def test_bytes_match_str(self):
        assert sha256_bytes(b"hello") == sha256_str("hello")

    def test_empty_bytes(self):
        result = sha256_bytes(b"")
        assert len(result) == 64


class TestSHA256File:
    def test_file_hash(self):
        with tempfile.NamedTemporaryFile(delete=False, mode="wb") as f:
            f.write(b"test content")
            path = f.name
        try:
            result = sha256_file(path)
            assert result == sha256_bytes(b"test content")
        finally:
            os.unlink(path)

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(delete=False, mode="wb") as f:
            path = f.name
        try:
            result = sha256_file(path)
            assert len(result) == 64
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        with pytest.raises((FileNotFoundError, OSError)):
            sha256_file("/nonexistent/path/file.txt")
