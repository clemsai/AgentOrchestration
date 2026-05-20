"""Regression tests for CLI deploy --dry-run flag (#535)."""

import json
import os
import subprocess
import sys

import pytest


def _run_cli(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "src.cli.main", *args],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


class TestCLIDeployDryRun:
    """Bounty #535: deploy --dry-run must validate manifest without deploying."""

    def test_dry_run_valid_manifest(self, tmp_path):
        manifest = tmp_path / "agent.json"
        manifest.write_text(json.dumps({"name": "test-agent"}))
        result = _run_cli(["deploy", str(manifest), "--dry-run"])
        assert result.returncode == 0
        assert "Dry run: manifest" in result.stdout
        assert "is valid" in result.stdout

    def test_dry_run_does_not_print_deploying(self, tmp_path):
        manifest = tmp_path / "agent.json"
        manifest.write_text(json.dumps({"name": "test-agent"}))
        result = _run_cli(["deploy", str(manifest), "--dry-run"])
        assert "Deploying agent" not in result.stdout

    def test_deploy_without_dry_run_prints_deploying(self, tmp_path):
        manifest = tmp_path / "agent.json"
        manifest.write_text(json.dumps({"name": "test-agent"}))
        result = _run_cli(["deploy", str(manifest)])
        assert result.returncode == 0
        assert "Deploying agent" in result.stdout

    def test_dry_run_nonexistent_manifest_fails(self, tmp_path):
        result = _run_cli(["deploy", str(tmp_path / "nope.json"), "--dry-run"])
        assert result.returncode != 0
        assert "manifest path does not exist" in result.stderr

    def test_dry_run_invalid_json_fails(self, tmp_path):
        manifest = tmp_path / "bad.json"
        manifest.write_text("not json {{{")
        result = _run_cli(["deploy", str(manifest), "--dry-run"])
        assert result.returncode != 0
        assert "not valid JSON" in result.stderr

    def test_dry_run_non_object_json_fails(self, tmp_path):
        manifest = tmp_path / "array.json"
        manifest.write_text(json.dumps([1, 2, 3]))
        result = _run_cli(["deploy", str(manifest), "--dry-run"])
        assert result.returncode != 0
        assert "must be a JSON object" in result.stderr
