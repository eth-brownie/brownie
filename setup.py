#!/usr/bin/python3
import os
import sys

from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

if os.environ.get("BROWNIE_LIB", "0") == "1":
    if sys.platform == "windows":
        requirements_filename = "requirements-windows.in"
    else:
        requirements_filename = "requirements.in"
else:
    if sys.platform == "windows":
        requirements_filename = "requirements-windows.txt"
    else:
        requirements_filename = "requirements.txt"

with open(requirements_filename, "r") as f:
    requirements = list(map(str.strip, f.read().split("\n")))[:-1]

try:
    from mypyc.build import mypycify
except ImportError:
    ext_modules = []
else:
    ext_modules = mypycify(
        [
            "brownie/_cli",
            "brownie/convert/__init__.py",
            "brownie/convert/main.py",
            "brownie/convert/normalize.py",
            "brownie/convert/utils.py",
            "brownie/network/__init__.py",
            "brownie/project/compiler",
            "brownie/utils/__init__.py",
            "brownie/utils/_color.py",
            "brownie/utils/output.py",
            "brownie/utils/sql.py",
            "brownie/utils/toposort.py",
            # "--strict",
            "--pretty",
            "--check-untyped-defs",
        ]
    )


setup(
    name="eth-brownie",
    packages=find_packages(),
    version="1.21.0",  # don't change this manually, use bumpversion instead
    license="MIT",
    description="A Python framework for Ethereum smart contract deployment, testing and interaction.",  # noqa: E501
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ben Hauser",
    author_email="ben@hauser.id",
    url="https://github.com/eth-brownie/brownie",
    keywords=["brownie"],
    install_requires=requirements,
    entry_points={
        "console_scripts": ["brownie=brownie._cli.__main__:main"],
        "pytest11": ["pytest-brownie=brownie.test.plugin"],
    },
    package_data={
        "brownie": ["py.typed"],
    },
    include_package_data=True,
    ext_modules=ext_modules,
    python_requires=">=3.10,<4",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
