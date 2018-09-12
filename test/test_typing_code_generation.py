from typing import Any

import pytest

from rest_client_gen.dynamic_typing import *

test_imports_compiler_data = [
    pytest.param(
        [
            ('typing', ('List', 'Any')),
            [],
            [],
            ('pytest', 'param')
        ],
        "from pytest import param\nfrom typing import Any, List",
        id="basic"
    )
]


@pytest.mark.parametrize("value,expected", test_imports_compiler_data)
def test_imports_compiler(value: ImportPathList, expected):
    code = compile_imports(value)
    assert code == expected


test_data = [
    pytest.param(
        UnknownType,
        Any,
        id="UnknownType"
    )
]

# @pytest.mark.parametrize("value,expected", test_data)
# def test_typing_code_generation(value: MetaData, expected):
#     imports, code = value.to_typing_code()
