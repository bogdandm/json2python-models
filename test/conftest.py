import pytest

from attrs_api.generator import Generator


@pytest.fixture(scope="module")
def models_generator():
    return Generator()
