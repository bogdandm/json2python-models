from collections import OrderedDict
from random import shuffle

import pytest

from attrs_api.dynamic_typing import DOptional, DUnion, NoneType
from attrs_api.generator import Generator

test_data = [
    pytest.param(
        [{'a': int}, {'a': int, 'b': int}],
        {'a': DUnion(int), 'b': DOptional(int)},
        id="optional_fields"
    ),
    pytest.param(
        [{'a': int}, {'a': float}],
        {'a': DUnion(int, float)},
        id="union"
    ),
    pytest.param(
        [{'a': DUnion(str, bool)}, {'a': float}],
        {'a': DUnion(str, bool, float)},
        id="merge_unions"
    ),
    pytest.param(
        [{'a': DUnion(str, bool)}, {'a': DUnion(int, float)}],
        {'a': DUnion(str, bool, int, float)},
        id="merge_unions2"
    ),
    # This functional is moved to _optimize_type
    # pytest.param(
    #     [{'d': {'x': int}}, {'d': {'x': NoneType}}],
    #     {'d': {'x': DUnion(int, NoneType)}},
    #     id="merge_nested"
    # )
]


@pytest.mark.parametrize("value,expected", test_data)
def test_merge_field_sets(models_generator: Generator, value, expected):
    shuffled = value[:]
    shuffle(shuffled)
    for v in (value, reversed(value), shuffled):
        result = models_generator._merge_field_sets(v)
        if isinstance(result, OrderedDict):
            result = dict(result)
        assert result == expected
