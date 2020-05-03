from typing import Dict, List

import pytest

from json_to_models.dynamic_typing import (
    DDict,
    DList,
    DOptional,
    DUnion,
    FloatString,
    IntString,
    ModelMeta,
    compile_imports,
)
from json_to_models.models.base import generate_code
from json_to_models.models.pydantic import PydanticModelCodeGenerator
from json_to_models.models.structure import sort_fields
from test.test_code_generation.test_models_code_generator import model_factory, trim

# Data structure:
# pytest.param id -> {
#   "model" -> (model_name, model_metadata),
#   test_name -> expected, ...
# }
test_data = {
    "base": {
        "model": ("Test", {
            "foo": int,
            "Bar": int,
            "baz": float
        }),
        "fields_data": {
            "foo": {
                "name": "foo",
                "type": "int"
            },
            "Bar": {
                "name": "bar",
                "type": "int",
                "body": 'Field(..., alias="Bar")'
            },
            "baz": {
                "name": "baz",
                "type": "float"
            }
        },
        "fields": {
            "imports": "",
            "fields": [
                f"foo: int",
                f'bar: int = Field(..., alias="Bar")',
                f"baz: float",
            ]
        },
        "generated": trim(f"""
        from pydantic import BaseModel, Field
        
        
        class Test(BaseModel):
            foo: int
            bar: int = Field(..., alias="Bar")
            baz: float
        """)
    },
    "complex": {
        "model": ("Test", {
            "foo": int,
            "baz": DOptional(DList(DList(str))),
            "bar": DOptional(IntString),
            "qwerty": FloatString,
            "asdfg": DOptional(int),
            "dict": DDict(int),
            "not": bool,
            "1day": int,
            "день_недели": str,
        }),
        "fields_data": {
            "foo": {
                "name": "foo",
                "type": "int"
            },
            "baz": {
                "name": "baz",
                "type": "Optional[List[List[str]]]",
                "body": "[]"
            },
            "bar": {
                "name": "bar",
                "type": "Optional[int]",
                "body": "None"
            },
            "qwerty": {
                "name": "qwerty",
                "type": "float"
            },
            "asdfg": {
                "name": "asdfg",
                "type": "Optional[int]",
                "body": "None"
            },
            "dict": {
                "name": "dict_",
                "type": "Dict[str, int]",
                "body": 'Field(..., alias="dict")'
            },
            "not": {
                "name": "not_",
                "type": "bool",
                "body": 'Field(..., alias="not")'
            },
            "1day": {
                "name": "one_day",
                "type": "int",
                "body": 'Field(..., alias="1day")'
            },
            "день_недели": {
                "name": "den_nedeli",
                "type": "str",
                "body": 'Field(..., alias="день_недели")'
            }
        },
        "generated": trim(f"""
        from pydantic import BaseModel, Field
        from typing import Dict, List, Optional


        class Test(BaseModel):
            foo: int
            qwerty: float
            dict_: Dict[str, int] = Field(..., alias="dict")
            not_: bool = Field(..., alias="not")
            one_day: int = Field(..., alias="1day")
            den_nedeli: str = Field(..., alias="день_недели")
            baz: Optional[List[List[str]]] = []
            bar: Optional[int] = None
            asdfg: Optional[int] = None
        """)
    },
    "converters": {
        "model": ("Test", {
            "a": int,
            "b": IntString,
            "c": DOptional(FloatString),
            "d": DList(DList(DList(IntString))),
            "e": DDict(IntString),
            "u": DUnion(DDict(IntString), DList(DList(IntString))),
        }),
        "generated": trim("""
        from pydantic import BaseModel, Field
        from typing import Dict, List, Optional, Union


        class Test(BaseModel):
            a: int
            b: int
            d: List[List[List[int]]]
            e: Dict[str, int]
            u: Union[Dict[str, int], List[List[int]]]
            c: Optional[float] = None
        """)
    }
}

test_data_unzip = {
    test: [
        pytest.param(
            model_factory(*data["model"]),
            data[test],
            id=id
        )
        for id, data in test_data.items()
        if test in data
    ]
    for test in ("fields_data", "fields", "generated")
}


@pytest.mark.parametrize("value,expected", test_data_unzip["fields_data"])
def test_fields_data_attr(value: ModelMeta, expected: Dict[str, dict]):
    gen = PydanticModelCodeGenerator(value)
    required, optional = sort_fields(value)
    for is_optional, fields in enumerate((required, optional)):
        for field in fields:
            field_imports, data = gen.field_data(field, value.type[field], bool(is_optional))
            assert data == expected[field]


@pytest.mark.parametrize("value,expected", test_data_unzip["fields"])
def test_fields_attr(value: ModelMeta, expected: dict):
    expected_imports: str = expected["imports"]
    expected_fields: List[str] = expected["fields"]
    gen = PydanticModelCodeGenerator(value)
    imports, fields = gen.fields
    imports = compile_imports(imports)
    assert imports == expected_imports
    assert fields == expected_fields


@pytest.mark.parametrize("value,expected", test_data_unzip["generated"])
def test_generated_attr(value: ModelMeta, expected: str):
    generated = generate_code(
        (
            [{"model": value, "nested": []}],
            {}
        ),
        PydanticModelCodeGenerator,
        class_generator_kwargs={}
    )
    assert generated.rstrip() == expected, generated
