"""Setup script for the Agentic AI Testing System."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="agentic-kernel-testing",
    version="0.1.0",
    author="Your Name",
    author_email="you@example.com",
    description="Agentic AI Testing System for Linux Kernel and BSP",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/agentic-kernel-testing",
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest-cov>=4.1.0",
            "pytest-asyncio>=0.21.0",
            "mypy>=1.7.0",
            "pylint>=3.0.0",
            "black>=23.11.0",
            "isort>=5.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "agentic-test=cli.main:main",
        ],
    },
)
