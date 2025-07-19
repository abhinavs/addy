#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="addy",
    version="1.0.2",
    author="Abhinav Saxena",
    author_email="abhinav@apiclabs.com",
    description="Simple user access management for Linux servers. Like apt install but for people.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/abhinavs/addy",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Systems Administration",
        "Topic :: Security",
    ],
    python_requires=">=3.8",
    install_requires=[
        "GitPython>=3.1.0",
        "click>=8.0.0",
        "cryptography>=3.4.0",
        "PyYAML>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "addy=addy.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
