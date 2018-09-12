from typing import Any, List, Optional, Tuple, Union

import pytest

from rest_client_gen.dynamic_typing import *


@pytest.mark.xfail(strict=True, raises=ValueError)
def test_metadata_to_typing_with_dict():
    metadata_to_typing({'a': 1})


test_imports_compiler_data = [
    pytest.param(
        [
            ('typing', ('List', 'Any')),
            [],
            [],
            ('pytest', 'param'),
            ('typing', ('List', 'Tuple')),
        ],
        "from pytest import param\nfrom typing import Any, List, Tuple",
        id="basic"
    )
]


@pytest.mark.parametrize("value,expected", test_imports_compiler_data)
def test_imports_compiler(value: ImportPathList, expected):
    code = compile_imports(value)
    assert code == expected


test_data = [
    pytest.param(
        UnknownType(),
        ('from typing import Any', Any),
        id="UnknownType"
    ),
    pytest.param(
        int,
        ('', int),
        id='builtin'
    ),
    pytest.param(
        DOptional(int),
        ('from typing import Optional', Optional[int]),
        id="DOptional"
    ),
    pytest.param(
        DOptional(UnknownType()),
        ('from typing import Any, Optional', Optional[Any]),
        id="DOptional_UnknownType"
    ),
    pytest.param(
        DUnion(int, DOptional(str)),
        ('from typing import Optional, Union', Union[int, Optional[str]]),
        id="DUnion"
    ),
    pytest.param(
        DTuple(int, DUnion(str, float)),
        ('from typing import Tuple, Union', Tuple[int, Union[str, float]]),
        id="DTuple"
    ),
    pytest.param(
        DList(DUnion(str, float)),
        ('from typing import List, Union', List[Union[str, float]]),
        id="DList"
    ),
    pytest.param(
        DList(DList(DList(DList(DUnion(str, float))))),
        ('from typing import List, Union', List[List[List[List[Union[str, float]]]]]),
        id="deep_DList"
    )
]


@pytest.mark.parametrize("value,expected", test_data)
def test_typing_code_generation(value: MetaData, expected):
    imports, code = metadata_to_typing(value)
    imports_code = compile_imports(imports)
    assert imports_code == expected[0]
    t = eval(code)
    assert t == expected[1]
