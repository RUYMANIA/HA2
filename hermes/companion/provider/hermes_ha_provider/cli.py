"""Command-line entry point for the companion service."""

from __future__ import annotations

import argparse
import json
import sys

from aiohttp import web

from .app import create_app
from .config import ConfigurationError, Settings
from .runtime import HermesRuntime, RuntimeFailure


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes provider companion for Home Assistant")
    parser.add_argument(
        "--probe",
        action="store_true",
        help="probe installed Hermes seams and print safe capability labels",
    )
    return parser


def main() -> None:
    """Validate configuration, optionally probe, then run aiohttp."""
    args = _parser().parse_args()
    try:
        settings = Settings.from_env()
        runtime = HermesRuntime(settings)
    except (ConfigurationError, RuntimeFailure) as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
    if args.probe:
        capabilities = runtime.capabilities()
        print(
            json.dumps(
                {
                    name: "Hermes configured provider" if enabled else "unavailable"
                    for name, enabled in capabilities.items()
                },
                sort_keys=True,
            )
        )
        return
    web.run_app(
        create_app(settings, runtime),
        host=settings.host,
        port=settings.port,
        access_log=None,
        print=None,
    )


if __name__ == "__main__":
    main()
