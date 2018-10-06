import pytest

from json_to_models.dynamic_typing import (BooleanString, DList, DOptional, DTuple, DUnion, FloatString, IntString,
                                           NoneType, Unknown)
from json_to_models.generator import MetadataGenerator

# MetaData | Optimized MetaData
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
        {'1': {'a': DOptional({'b': float})}},
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
    pytest.param(
        DUnion(FloatString, str),
        str,
        id="union_str_str_based"
    ),
    pytest.param(
        DUnion(DList(int), DList(str), str),
        DUnion(DList(DUnion(int, str)), str),
        id="union_of_lists"
    ),
    pytest.param(
        DUnion(Unknown, str),
        str,
        id="unknown_vs_single"
    ),
    pytest.param(
        DUnion(Unknown, str, int),
        DUnion(str, int),
        id="unknown_vs_multi"
    ),
    pytest.param(
        DUnion(DList(Unknown), DList(str)),
        DList(str),
        id="list_unknown_vs_single"
    ),
    pytest.param(
        DUnion(DList(Unknown), DList(str), DList(int)),
        DList(DUnion(str, int)),
        id="list_unknown_vs_multi"
    ),
    pytest.param(
        DUnion(NoneType, str),
        DOptional(str),
        id="optional_str"
    ),
    pytest.param(
        DUnion(NoneType, DList(str)),
        DOptional(DList(str)),
        id="optional_list"
    ),
    pytest.param(
        DList(DUnion(NoneType, str)),
        DList(DOptional(str)),
        id="list_of_optional_strings"
    ),
    pytest.param(
        DUnion(NoneType, DList(str), int),
        DOptional(DUnion(DList(str), int)),
        id="optional_list_or_int"
    ),
    pytest.param(
        DUnion(NoneType, DList(DUnion(str, int))),
        DOptional(DList(DUnion(str, int))),
        id="optional_list_of_str_or_int"
    ),
    pytest.param(
        DList(DUnion(NoneType, str, int)),
        DList(DOptional(DUnion(str, int))),
        id="list_of_optional_strings_ot_int"
    ),
    pytest.param(
        DList(DUnion(str, int, FloatString, IntString)),
        DList(DUnion(str, int)),
        id="union_of_str_int_FloatString"
    ),
]


@pytest.mark.parametrize("value,expected", test_data)
def test_optimize_type(models_generator: MetadataGenerator, value, expected):
    result = models_generator.optimize_type(value)
    assert result == expected
