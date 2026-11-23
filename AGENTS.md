# Agent Requirements

All agents must follow these rules:

brownie is always compiled. PyPI wheels are compiled, setup compiles the project, and tests/CI must validate compiled extensions. Do not invent or reason from an interpreted `.py` runtime path; tracked `.py` files are mypyc source inputs.
