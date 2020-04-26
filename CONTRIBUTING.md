# Development

To start development for Brownie you should begin by cloning the repo. We highly recommend using [`venv`](https://docs.python.org/3/library/venv.html) and installing into a fresh virtual environment.

```bash
git clone https://github.com/iamdefinitelyahuman/brownie.git
```

Next, ensure all dev dependencies have been installed:

```bash
pip install -r requirements-dev.txt
```

## Pre-Commit Hooks

We use [`pre-commit`](https://pre-commit.com/) hooks to simplify linting and ensure consistent formatting among contributors. Use of `pre-commit` is not a requirement, but is highly recommended.

Install `pre-commit` locally from the brownie root folder:

```bash
pip install pre-commit
pre-commit install
```

Commiting will now automatically run the local hooks and ensure that your commit passes all lint checks.

## Pull Requests

Pull requests are welcomed! Please adhere to the following:

- Ensure your pull request passes our linting checks (`tox -e lint`)
- Include test cases for any new functionality
- Include any relevant documentation updates

It's a good idea to make pull requests early on. A pull request represents the start of a discussion, and doesn't necessarily need to be the final, finished submission.

If you are opening a work-in-progress pull request to verify that it passes CI tests, please consider [marking it as a draft](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/about-pull-requests#draft-pull-requests).

Join the Brownie [Gitter channel](https://gitter.im/eth-brownie/community) if you have any questions.
