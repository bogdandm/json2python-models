import pytest

from json_to_models.dynamic_typing import BooleanString, DList, DUnion, FloatString, IntString, NoneType, Unknown
from json_to_models.generator import MetadataGenerator

# JSON data | MetaData
test_data = [
    pytest.param(1.0, float, id="float"),
    pytest.param(1, int, id="int"),
    pytest.param(True, bool, id="bool"),
    pytest.param("abc", str, id="str"),
    pytest.param(None, NoneType, id="null"),
    pytest.param([], DList(Unknown), id="list_empty"),
    pytest.param([1], DList(int), id="list_single"),
    pytest.param([*range(100)], DList(int), id="list_single_type"),
    pytest.param([1, "a", 2, "c"], DList(DUnion(int, str)), id="list_multi"),
    pytest.param("1", IntString, id="int_str"),
    pytest.param("1.0", FloatString, id="float_str"),
    pytest.param("true", BooleanString, id="bool_str"),
]

test_dict = {param.id: param.values[0] for param in test_data}
test_dict_meta = {param.id: param.values[1] for param in test_data}

test_dict_nested = {"b": {"d": test_dict}}
test_dict_nested_meta = {"b": {"d": test_dict_meta}}

test_data += [
    pytest.param(test_dict, test_dict_meta, id="flat_dict"),
    pytest.param(test_dict_nested, test_dict_nested_meta, id="dict"),
]


@pytest.mark.parametrize("value,expected", test_data)
def test_detect_type(models_generator: MetadataGenerator, value, expected):
    assert models_generator._detect_type(value) == expected
