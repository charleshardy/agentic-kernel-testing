#!/usr/bin/env python3
"""Setup script for CLI installation."""

from setuptools import setup, find_packages
from pathlib import Path

# Read version from __init__.py
init_file = Path(__file__).parent / "__init__.py"
version = "1.0.0"
for line in init_file.read_text().splitlines():
    if line.startswith("__version__"):
        version = line.split("=")[1].strip().strip('"').strip("'")
        break

# Read requirements
requirements = [
    "click>=8.0.0",
    "requests>=2.25.0",
    "pydantic>=1.8.0",
    "python-dotenv>=0.19.0",
    "PyYAML>=6.0",
]

setup(
    name="agentic-testing-cli",
    version=version,
    description="Command-line interface for the Agentic AI Testing System",
    long_description="A comprehensive CLI for managing kernel and BSP testing workflows",
    author="Agentic Testing Team",
    packages=find_packages(),
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "agentic-test=cli.main:cli",
            "agentic=cli.main:cli",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)