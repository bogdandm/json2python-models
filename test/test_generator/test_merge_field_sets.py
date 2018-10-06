from collections import OrderedDict
from random import shuffle

import pytest

from json_to_models.dynamic_typing import DOptional, DUnion, FloatString, IntString
from json_to_models.generator import MetadataGenerator

# List of fields sets | result field set
test_data = [
    pytest.param(
        [{'a': int}, {'a': int, 'b': int}],
        {'a': int, 'b': DOptional(int)},
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
    pytest.param(
        [{'a': int}, {}, {'a': int}, {}],
        {'a': DOptional(int)},
        id="merge_optional_int"
    ),
    pytest.param(
        [{'a': str}, {}, {'a': int}, {}],
        {'a': DOptional(DUnion(str, int))},
        id="merge_optional_str_int"
    ),
    pytest.param(
        [{'a': DUnion(int)}, {}, {'a': int}, {}],
        {'a': DOptional(int)},
        id="merge_optional_single_union"
    ),
    pytest.param(
        [{'a': DUnion(int)}, {'a': int}],
        {'a': int},
        id="merge_single_union"
    ),
    pytest.param(
        [
            {'a': DUnion(int, str)},
            {'a': DUnion(int, FloatString)},
            {'a': DUnion(int, IntString)},
            {'a': DUnion(int, str)},
            {'a': DUnion(int, IntString)},
            {'a': DUnion(int, str)},
            {'a': DUnion(int, FloatString)},
            {'a': DUnion(int, IntString)},
            {'a': DUnion(int, str)},
            {'a': DUnion(int, IntString)},
        ],
        {'a': DUnion(int, str, FloatString, IntString)},
        id="merge_unions_of_pseudo_strings"
    ),
    pytest.param(
        [
            {'a': int},
            {},
            {'a': DOptional(int)},
        ],
        {'a': DOptional(int)},
        id="merge_optionals_and_nulls"
    ),
    # This functional is moved to _optimize_type
    # pytest.param(
    #     [{'d': {'x': int}}, {'d': {'x': NoneType}}],
    #     {'d': {'x': DUnion(int, NoneType)}},
    #     id="merge_nested"
    # )
]


@pytest.mark.parametrize("value,expected", test_data)
def test_merge_field_sets(models_generator: MetadataGenerator, value, expected):
    shuffled = value[:]
    shuffle(shuffled)
    for v in (value, reversed(value), shuffled):
        result = models_generator.merge_field_sets(v)
        if isinstance(result, OrderedDict):
            result = dict(result)
        assert result == expected
