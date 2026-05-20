"""Regression tests for CLI deploy manifest validation (#562)."""

import os
import subprocess
import sys

import pytest


class TestCLIDeployManifestValidation:
    """Bounty #562: CLI must validate the manifest path before reporting progress."""

    def _run_cli(self, args: list[str]) -> subprocess.CompletedProcess:
        """Run the CLI module as a subprocess to capture exit codes."""
        return subprocess.run(
            [sys.executable, "-m", "src.cli.main", *args],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

    def test_deploy_nonexistent_manifest_exits_nonzero(self, tmp_path):
        manifest = str(tmp_path / "no_such_file.yaml")
        result = self._run_cli(["deploy", manifest])
        assert result.returncode != 0, "Should exit non-zero for missing manifest"

    def test_deploy_nonexistent_manifest_prints_error(self, tmp_path):
        manifest = str(tmp_path / "no_such_file.yaml")
        result = self._run_cli(["deploy", manifest])
        assert "Error" in result.stderr, f"Expected error on stderr, got: {result.stderr}"
        assert manifest in result.stderr

    def test_deploy_nonexistent_manifest_no_deploy_message(self, tmp_path):
        manifest = str(tmp_path / "no_such_file.yaml")
        result = self._run_cli(["deploy", manifest])
        assert "Deploying agent" not in result.stdout, "Should not print deploy message for missing manifest"

    def test_deploy_existing_manifest_succeeds(self, tmp_path):
        manifest = tmp_path / "agent.yaml"
        manifest.write_text("name: test-agent\n")
        result = self._run_cli(["deploy", str(manifest)])
        assert result.returncode == 0, f"Should succeed for existing manifest, got: {result.stderr}"
        assert "Deploying agent" in result.stdout
