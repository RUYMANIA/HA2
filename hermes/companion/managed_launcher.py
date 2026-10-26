"""Enter the current Hermes-managed runtime without changing its dependencies."""
import json
import os
from pathlib import Path
import subprocess
import sys


def script_command(runtime_command, script, arguments):
    command = list(runtime_command)
    marker = "runpy.run_module('hermes_cli.main'"
    if len(command) < 4 or command[-2] != '-c' or marker not in command[-1]:
        raise RuntimeError('Unexpected Hermes bootstrap; refusing to guess')
    argv = [str(script), *arguments]
    command[-1] = command[-1].split(marker, 1)[0] + (
        f'sys.argv={argv!r}; runpy.run_path({str(script)!r},run_name="__main__")'
    )
    return command


def main():
    root = Path(__file__).resolve().parent
    launcher = Path.home() / '.hermes/hermes-agent/.hermes/bin/hermes'
    runtime = json.loads(subprocess.check_output(
        [str(launcher), '--print-runtime-command'], text=True, timeout=45
    ))
    command = script_command(runtime, root / 'run_provider.py', sys.argv[1:])
    os.execv(command[0], command)


if __name__ == '__main__':
    main()
