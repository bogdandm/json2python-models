import pytest

from rest_client_gen.generator import Generator


@pytest.fixture(scope="module")
def models_generator():
    return Generator()
