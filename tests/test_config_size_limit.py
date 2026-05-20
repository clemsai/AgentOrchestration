"""Regression tests for config file size limit (#738)."""

import os
import json

import pytest

from src.common.config import Config, ConfigSizeError, MAX_CONFIG_SIZE


class TestConfigSizeLimit:
    """Bounty #738: Config.load must reject files exceeding the documented maximum size."""

    def test_load_normal_config(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text('{"app": {"name": "test"}}')
        config = Config(str(config_file))
        assert config.get("app.name") == "test"

    def test_reject_oversized_file(self, tmp_path):
        """A config file larger than MAX_CONFIG_SIZE must raise ConfigSizeError."""
        config_file = tmp_path / "big.json"
        # Write a file slightly over the limit
        size = MAX_CONFIG_SIZE + 1
        with open(config_file, "wb") as f:
            f.write(b" " * size)
        with pytest.raises(ConfigSizeError, match="exceeds the maximum allowed size"):
            Config(str(config_file))

    def test_reject_oversized_file_exact_boundary(self, tmp_path):
        """A config file exactly at the limit + 1 must be rejected."""
        config_file = tmp_path / "boundary.json"
        with open(config_file, "wb") as f:
            f.write(b" " * (MAX_CONFIG_SIZE + 1))
        with pytest.raises(ConfigSizeError):
            Config(str(config_file))

    def test_accept_file_at_exact_limit(self, tmp_path):
        """A config file exactly at the limit must be accepted."""
        config_file = tmp_path / "exact.json"
        # Create a small valid JSON file and pad it to exactly MAX_CONFIG_SIZE
        inner = json.dumps({"k": "v"})
        # Pad with spaces (valid whitespace in JSON) to reach exact size
        padding = MAX_CONFIG_SIZE - len(inner)
        raw = " " * padding + inner
        config_file.write_text(raw)
        assert os.path.getsize(str(config_file)) == MAX_CONFIG_SIZE
        # Should not raise
        config = Config(str(config_file))
        assert config.get("k") == "v"

    def test_size_check_before_parsing(self, tmp_path):
        """Ensure the size check happens before json.load to prevent memory exhaustion."""
        config_file = tmp_path / "huge.json"
        # Write a file that is not valid JSON and is oversized
        size = MAX_CONFIG_SIZE + 100
        with open(config_file, "wb") as f:
            f.write(b"\x00" * size)
        # Should get ConfigSizeError, not json.JSONDecodeError
        with pytest.raises(ConfigSizeError):
            Config(str(config_file))
