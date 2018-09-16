import pytest

from rest_client_gen.generator import MetadataGenerator
from rest_client_gen.registry import ModelRegistry


@pytest.fixture
def models_generator():
    return MetadataGenerator()


@pytest.fixture
def models_registry():
    return ModelRegistry()
