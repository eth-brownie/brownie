#!/usr/bin/python3

from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name = 'eth-brownie',
    packages=find_packages(),
    package_data={'': ['**/*.py','**/**/*.py', 'data/config.json']},
    version = '1.0.3b',
    license = 'MIT',
    description = 'A python framework for testing, deploying and interacting with Ethereum smart contracts.',
    long_description = long_description,
    long_description_content_type = "text/markdown",
    author = 'Benjamin Hauser',
    author_email = 'ben.hauser@hyperlink.technology',
    url = 'https://github.com/HyperLink-Technology/brownie',
    download_url = 'https://github.com/HyperLink-Technology/brownie/archive/v1.0.0b.tar.gz',
    keywords = ['brownie'],
    install_requires = [
        "attrdict==2.0.1",
        "certifi==2019.3.9",
        "chardet==3.0.4",
        "cytoolz==0.9.0.1",
        "docopt==0.6.2",
        "eth-abi==1.3.0",
        "eth-account==0.3.0",
        "eth-event==0.1.4",
        "eth-hash==0.2.0",
        "eth-keyfile==0.5.1",
        "eth-keys==0.2.1",
        "eth-rlp==0.1.2",
        "eth-typing==2.1.0",
        "eth-utils==1.4.1",
        "hexbytes==0.1.0",
        "idna==2.8",
        "lru-dict==1.1.6",
        "parsimonious==0.8.1",
        "py-solc-x==0.1.1",
        "pycryptodome==3.8.1",
        "requests==2.21.0",
        "rlp==1.1.0",
        "semantic-version==2.6.0",
        "six==1.12.0",
        "toolz==0.9.0",
        "urllib3==1.24.1",
        "web3==4.9.1",
        "websockets==6.0",
    ],
    entry_points = {"console_scripts": ["brownie=brownie.cli:__main__"]},
    include_package_data = True,
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7'
    ],
) 
