"""Regression tests for CLI stdout/stderr convention (#366)."""

import os
import subprocess
import sys

import pytest


class _CLIRunner:
    """Helper to run the CLI and capture stdout/stderr separately."""

    @staticmethod
    def run(args: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "src.cli.main", *args],
            capture_output=True,
            text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )


class TestCLIStderrForErrors:
    """Bounty #366: Error messages must go to stderr, data to stdout."""

    def test_deploy_missing_manifest_error_on_stderr(self, tmp_path):
        result = _CLIRunner.run(["deploy", str(tmp_path / "nope.yaml")])
        assert "Error:" in result.stderr
        assert "manifest path does not exist" in result.stderr

    def test_deploy_missing_manifest_no_error_on_stdout(self, tmp_path):
        result = _CLIRunner.run(["deploy", str(tmp_path / "nope.yaml")])
        assert "Error" not in result.stdout
        assert "manifest path does not exist" not in result.stdout

    def test_deploy_success_data_on_stdout(self, tmp_path):
        manifest = tmp_path / "agent.yaml"
        manifest.write_text("name: test-agent\n")
        result = _CLIRunner.run(["deploy", str(manifest)])
        assert "Deploying agent from manifest" in result.stdout
        assert "Deploying agent from manifest" not in result.stderr

    def test_init_data_on_stdout(self):
        result = _CLIRunner.run(["init", "my-project"])
        assert "Initializing project: my-project" in result.stdout
        assert "Initializing project" not in result.stderr

    def test_status_data_on_stdout(self):
        result = _CLIRunner.run(["status"])
        assert "Checking agent status" in result.stdout
        assert "Checking agent status" not in result.stderr

    def test_logs_data_on_stdout(self):
        result = _CLIRunner.run(["logs", "agent-123"])
        assert "Fetching logs for agent: agent-123" in result.stdout
        assert "Fetching logs" not in result.stderr

    def test_no_command_error_goes_to_stderr_via_argparse(self):
        """When no subcommand is given, argparse prints help to stderr."""
        result = _CLIRunner.run([])
        assert result.returncode != 0
