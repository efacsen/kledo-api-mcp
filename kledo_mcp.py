#!/usr/bin/env python3
"""
Entry point script for Kledo MCP Server.
This script handles both direct execution and module imports.
"""

import sys
import subprocess
from pathlib import Path

# Add project root to sys.path so `from src.X import` works when running
# directly (e.g. `python kledo_mcp.py`). When installed via pip/uv the
# package is already discoverable and this is a no-op.
_project_root = str(Path(__file__).parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

def main():
    """Entry point with first-run detection and CLI support."""
    import os
    import asyncio

    # Import CLI and setup components
    from src.cli import parse_args, dispatch_command
    from src.setup import SetupWizard
    from src.config_manager import ConfigManager

    # Parse command-line arguments
    args = parse_args(sys.argv[1:])

    # If command specified, dispatch it
    if any([args.setup, args.test, args.show_config, args.init, args.version]):
        return dispatch_command(args)

    # No command: check configuration status
    config_manager = ConfigManager()

    # Check if already configured (env vars or .env file)
    if config_manager.has_env_vars_configured():
        # Already configured via environment variables - start server
        pass
    elif config_manager.env_file_exists():
        # Already configured via .env file - start server
        pass
    else:
        # Not configured - run setup wizard
        wizard = SetupWizard()
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
