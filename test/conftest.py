import pytest

from rest_client_gen.generator import Generator
from rest_client_gen.registry import ModelRegistry


@pytest.fixture
def models_generator():
    return Generator()


@pytest.fixture
def models_registry():
    return ModelRegistry()
