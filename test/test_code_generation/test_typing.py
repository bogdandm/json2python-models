from random import randint
from typing import Any, List, Optional, Tuple, Union

import pytest

from json_to_models.dynamic_typing import *


@pytest.mark.xfail(strict=True, raises=ValueError)
def test_metadata_to_typing_with_dict():
    assert metadata_to_typing({'a': 1})


test_imports_compiler_data = [
    pytest.param(
        [
            ('typing', ('List', 'Any')),
            [],
            [],
            ('pytest', 'param'),
            ('typing', ('List', 'Tuple')),
        ],
        "from pytest import param\n"
        "from typing import Any, List, Tuple",
        id="basic"
    ),
    pytest.param(
        [
            ('typing', ('List', 'Any')),
            [],
            ('typing', None),
            [],
            ('pytest', 'param'),
            ('typing', ('List', 'Tuple')),
            ('attr', None),
            ('typing', None),
        ],
        "import attr\n"
        "import typing\n"
        "from pytest import param\n"
        "from typing import Any, List, Tuple",
        id="basic"
    ),
]


@pytest.mark.parametrize("value,expected", test_imports_compiler_data)
def test_imports_compiler(value: ImportPathList, expected):
    code = compile_imports(value)
    assert code == expected


def model(data: dict, name: str):
    meta = ModelMeta(data, str(randint(0, 1000)))
    meta.set_raw_name(name)
    return ModelPtr(meta)


class TestModel:
    pass


# MetaData | Tuple[import_stmnt, type]
test_data = [
    pytest.param(
        Unknown,
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
        DOptional(Unknown),
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
    ),
    pytest.param(
        FloatString,
        ('from json_to_models.dynamic_typing import FloatString', FloatString),
        id="string_serializable"
    ),
    pytest.param(
        DOptional(IntString),
        ('from json_to_models.dynamic_typing import IntString\n'
         'from typing import Optional', Optional[IntString]),
        id="complex_string_serializable"
    ),
    pytest.param(
        model({'a': int}, "TestModel"),
        ('', 'TestModel')
    ),
    pytest.param(
        DOptional(model({'a': int}, "TestModel")),
        ('from typing import Optional', Optional['TestModel'])
    )
]


@pytest.mark.parametrize("value,expected", test_data)
def test_typing_code_generation(value: MetaData, expected):
    imports, code = metadata_to_typing(value)
    imports_code = compile_imports(imports)
    assert imports_code == expected[0]
    t = eval(code)
    assert t == expected[1]
