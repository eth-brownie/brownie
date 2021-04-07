# Development

To get started with working on the Brownie codebaser, use the following steps prepare your local environment:

```bash
# clone the github repo and navigate into the folder
git clone https://github.com/eth-brownie/brownie.git
cd brownie

# create and load a virtual environment
python3 -m venv venv
source venv/bin/activate

# install brownie into the virtual environment
python setup.py install

# install the developer dependencies
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

## Productivity Tips

### Running Tests

Instead of running the entire test suite each time you make a change, run specific tests and fail fast (`-x`):

```bash
docker-compose exec sandbox bash -c 'python -m pytest tests/project/test_brownie_config.py::TestFooBar -x'
```

Drop to a pdb shell upon error with the `--pdb` flag:

```sh
docker-compose exec sandbox bash -c 'python -m pytest tests/project/test_brownie_config.py -x --pdb'
```
