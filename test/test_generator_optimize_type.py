from collections import OrderedDict

import pytest

from attrs_api.dynamic_typing import DUnion, NoneType
from attrs_api.generator import Generator

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
    )
]


@pytest.mark.parametrize("value,expected", test_data)
def test_optimize_type(models_generator: Generator, value, expected):
    result = models_generator._optimize_type(value)
    assert result == expected
