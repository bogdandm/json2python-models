import pytest

from rest_client_gen.dynamic_typing import DUnion, NoneType, FloatString, IntString, BooleanString, DList, DTuple
from rest_client_gen.generator import Generator

test_data = [
    pytest.param(DUnion(int), int, id="single_DUnion"),
    pytest.param(
        {'a': DUnion({'b': int}, {'b': float})},
        {'a': {'b': float}},
        id="merge_nested_dicts"
    ),
    pytest.param(
        {'1': DUnion(
            {'a': DUnion({'b': int}, {'b': float})},
            {'a': DUnion({'b': float}, {'b': int})},
            {'a': NoneType},
        )},
        {'1': {'a': DUnion(NoneType, {'b': float})}},
        id="merge_nested_dicts"
    ),
    pytest.param(
        DUnion(FloatString, IntString),
        FloatString,
        id="str_types_merge"
    ),
    pytest.param(
        DUnion(FloatString, BooleanString),
        str,
        id="str_types_merge_not_resolved"
    ),
    pytest.param(
        DList(DUnion(FloatString, BooleanString)),
        DList(str),
        id="str_types_merge_not_resolved_simple_wrapper"
    ),
    pytest.param(
        DTuple(DUnion(FloatString, BooleanString), int),
        DTuple(str, int),
        id="str_types_merge_not_resolved_complex_wrapper"
    ),
]


@pytest.mark.parametrize("value,expected", test_data)
def test_optimize_type(models_generator: Generator, value, expected):
    result = models_generator._optimize_type(value)
    assert result == expected
