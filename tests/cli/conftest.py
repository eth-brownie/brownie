import pytest
from click.testing import CliRunner


@pytest.fixture()
def runner():
    yield CliRunner()
