from builtins import complex

import pytest

from json_to_models.dynamic_typing import DUnion, get_hash_string

# *args | MetaData
test_dunion = [
    pytest.param(
        [int, int],
        DUnion(int),
        id="unique_types"
    ),
    pytest.param(
        [int, DUnion(int)],
        DUnion(int),
        id="nested_union_&_merge"
    ),
    pytest.param(
        [str, DUnion(int, DUnion(float, complex))],
        DUnion(int, float, complex, str),
        id="complex_merge"
    )
]


@pytest.mark.parametrize("value,expected", test_dunion)
def test_dunion_creation(value, expected):
    result = DUnion(*value)
    assert result == expected


def test_hash_string():
    a = {'a': int}
    b = {'b': int}
    c = {'a': float}
    assert len(set(map(get_hash_string, (a, b, c)))) == 3

    union = DUnion(str, float)
    h1 = union.to_hash_string()
    union.replace(complex, index=0)
    h2 = union.to_hash_string()
    assert h1 != h2, f"{h1}, {h2}"
