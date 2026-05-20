"""CLI entry point for the agent orchestrator."""

import argparse
import json
import os
import sys

from src.common.config import Config
from src.common.logging import configure_logging


def print_error(message: str) -> None:
    """Print an error message to stderr."""
    print(f"Error: {message}", file=sys.stderr)


def print_data(message: str) -> None:
    """Print data output to stdout."""
    print(message, file=sys.stdout)


def _validate_manifest(path: str) -> dict:
    """Validate a manifest file and return its parsed content.

    Raises SystemExit on validation failure.
    """
    if not os.path.exists(path):
        print_error(f"manifest path does not exist: {path}")
        sys.exit(1)
    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        print_error(f"manifest is not valid JSON: {exc}")
        sys.exit(1)
    if not isinstance(data, dict):
        print_error("manifest must be a JSON object")
        sys.exit(1)
    return data


def cli():
    parser = argparse.ArgumentParser(description="Agent Orchestrator CLI")
    parser.add_argument("--config", "-c", help="Path to config file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    init_parser = subparsers.add_parser("init", help="Initialize a new project")
    init_parser.add_argument("name", help="Project name")

    deploy_parser = subparsers.add_parser("deploy", help="Deploy an agent")
    deploy_parser.add_argument("manifest", help="Path to agent manifest file")
    deploy_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the manifest without deploying",
    )

    status_parser = subparsers.add_parser("status", help="Show agent status")
    status_parser.add_argument("--watch", "-w", action="store_true", help="Watch mode")

    logs_parser = subparsers.add_parser("logs", help="View agent logs")
    logs_parser.add_argument("agent_id", help="Agent ID")
    logs_parser.add_argument("--tail", "-t", type=int, default=50, help="Number of lines")

    args = parser.parse_args()

    if args.verbose:
        configure_logging("DEBUG")
    else:
        configure_logging("INFO")

    if args.command == "init":
        print_data(f"Initializing project: {args.name}")
    elif args.command == "deploy":
        manifest_data = _validate_manifest(args.manifest)
        if args.dry_run:
            print_data(f"Dry run: manifest {args.manifest} is valid")
        else:
            print_data(f"Deploying agent from manifest: {args.manifest}")
    elif args.command == "status":
        print_data("Checking agent status...")
    elif args.command == "logs":
        print_data(f"Fetching logs for agent: {args.agent_id}")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    cli()
