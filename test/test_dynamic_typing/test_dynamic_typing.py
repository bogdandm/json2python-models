import pytest

from rest_client_gen.dynamic_typing import DUnion

# *args | MetaData
test_dunion= [
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