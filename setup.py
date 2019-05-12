#!/usr/bin/python3

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as f:
    requirements = list(map(str.strip, f.read().split("\n")))[:-1]

setup(
    name="eth-brownie",
    packages=find_packages(),
    version="1.0.0b5",
    license="MIT",
    description="A Python framework for Ethereum smart contract deployment, testing and interaction.",  # noqa: E501
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Benjamin Hauser",
    author_email="ben.hauser@hyperlink.technology",
    url="https://github.com/HyperLink-Technology/brownie",
    keywords=['brownie'],
    install_requires=requirements,
    entry_points={'console_scripts': ["brownie=brownie.cli.__main__:main"]},
    include_package_data=True,
    python_requires=">=3.6,<4",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7"
    ],
)
