#!/usr/bin/python3

from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as f:
    requirements = list(map(str.strip, f.read().split("\n")))[:-1]

setup(
    name="eth-brownie",
    packages=find_packages(),
    version="1.11.9",  # don't change this manually, use bumpversion instead
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
    include_package_data=True,
    python_requires=">=3.6,<4",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
)
