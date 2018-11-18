import pytest

from json_to_models.generator import MetadataGenerator
from json_to_models.registry import ModelRegistry


@pytest.fixture
def models_generator():
    return MetadataGenerator(dict_keys_regex=[r"^test_dict_field_\w+$"], dict_keys_fields=["dict_field"])


@pytest.fixture
def models_registry():
    return ModelRegistry()
