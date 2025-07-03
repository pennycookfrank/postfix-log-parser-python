#!/usr/bin/env python3
"""
Setup script for postfix-log-parser-python
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="postfix-log-parser-python",
    version="1.0.0",
    author="Python Port",
    description="Parse postfix log files and output structured JSON format",
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["postfix_log_parser"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Logging",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "postfix-log-parser-python=postfix_log_parser:main",
        ],
    },
)
