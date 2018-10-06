import pytest

from json_to_models.generator import MetadataGenerator
from json_to_models.registry import ModelRegistry


@pytest.fixture
def models_generator():
    return MetadataGenerator()


@pytest.fixture
def models_registry():
    return ModelRegistry()
