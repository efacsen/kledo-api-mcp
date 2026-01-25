#!/usr/bin/env python3
"""
Fallback setup.py for compatibility with older Python versions and tools.
"""
from setuptools import setup

if __name__ == "__main__":
    # This setup.py is a fallback - the main configuration is in pyproject.toml
    # It will read the configuration from pyproject.toml automatically
    setup()
