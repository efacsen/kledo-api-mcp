#!/usr/bin/env python3
"""
Entry point script for Kledo MCP Server.
This script handles both direct execution and module imports.
"""

import sys
import subprocess
from pathlib import Path

# Add src directory to Python path for imports
src_dir = Path(__file__).parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

def main():
    """Entry point with first-run detection and CLI support."""
    import os
    import asyncio

    # Import CLI and setup components
    from src.cli import parse_args, dispatch_command
    from src.setup import SetupWizard

    # Parse command-line arguments
    args = parse_args(sys.argv[1:])

    # If command specified, dispatch it
    if any([args.setup, args.test, args.show_config, args.init, args.version]):
        return dispatch_command(args)

    # No command: check first-run
    wizard = SetupWizard()
    if wizard.detect_first_run():
        print("\n🚀 Welcome to Kledo MCP Server!")
        print("Let's set up your connection to Kledo API.\n")

        # Run setup wizard asynchronously
        try:
            success = asyncio.run(wizard.run())
            if success:
                print("\n✓ Setup complete! Starting server...\n")
            else:
                print("\n✗ Setup failed. Please try again.")
                return 1
        except KeyboardInterrupt:
            print("\n\n⚠ Setup cancelled by user.")
            return 1
        except Exception as e:
            print(f"\n✗ Setup failed: {str(e)}")
            return 1

    # Start server (keep existing subprocess pattern)
    try:
        # Get the directory containing this script
        script_dir = Path(__file__).parent
        src_dir = script_dir / "src"

        # Set up environment to ensure proper imports
        env = os.environ.copy()
        if 'PYTHONPATH' in env:
            env['PYTHONPATH'] = f"{str(src_dir)}:{env['PYTHONPATH']}"
        else:
            env['PYTHONPATH'] = str(src_dir)

        # Run python -m src.server as a subprocess
        # This ensures proper module isolation and relative imports
        result = subprocess.run([
            sys.executable, "-m", "src.server"
        ], cwd=script_dir, env=env)

        return result.returncode

    except FileNotFoundError:
        print("Python executable not found", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
