from typing import Dict, List

import pytest

from json_to_models.dynamic_typing import (DDict, DList, DOptional, FloatString, IntString, ModelMeta, compile_imports)
from json_to_models.models import sort_fields
from json_to_models.models.base import METADATA_FIELD_NAME, generate_code
from json_to_models.models.dataclasses import DataclassModelCodeGenerator
from test.test_code_generation.test_models_code_generator import model_factory, trim


def field_meta(original_name):
    return f"metadata={{'{METADATA_FIELD_NAME}': '{original_name}'}}"


# Data structure:
# pytest.param id -> {
#   "model" -> (model_name, model_metadata),
#   test_name -> expected, ...
# }
test_data = {
    "base": {
        "model": ("Test", {
            "foo": int,
            "bar": int,
            "baz": float
        }),
        "fields_data": {
            "foo": {
                "name": "foo",
                "type": "int",
                "body": f"field({field_meta('foo')})"
            },
            "bar": {
                "name": "bar",
                "type": "int",
                "body": f"field({field_meta('bar')})"
            },
            "baz": {
                "name": "baz",
                "type": "float",
                "body": f"field({field_meta('baz')})"
            }
        },
        "fields": {
            "imports": "",
            "fields": [
                f"foo: int = field({field_meta('foo')})",
                f"bar: int = field({field_meta('bar')})",
                f"baz: float = field({field_meta('baz')})",
            ]
        },
        "generated": trim(f"""
        from dataclasses import dataclass, field


        @dataclass
        class Test:
            foo: int = field({field_meta('foo')})
            bar: int = field({field_meta('bar')})
            baz: float = field({field_meta('baz')})
        """)
    },
    "complex": {
        "model": ("Test", {
            "foo": int,
            "baz": DOptional(DList(DList(str))),
            "bar": DOptional(IntString),
            "qwerty": FloatString,
            "asdfg": DOptional(int),
            "dict": DDict(int)
        }),
        "fields_data": {
            "foo": {
                "name": "foo",
                "type": "int",
                "body": f"field({field_meta('foo')})"
            },
            "baz": {
                "name": "baz",
                "type": "Optional[List[List[str]]]",
                "body": f"field(default_factory=list, {field_meta('baz')})"
            },
            "bar": {
                "name": "bar",
                "type": "Optional[IntString]",
                "body": f"field(default=None, {field_meta('bar')})"
            },
            "qwerty": {
                "name": "qwerty",
                "type": "FloatString",
                "body": f"field({field_meta('qwerty')})"
            },
            "asdfg": {
                "name": "asdfg",
                "type": "Optional[int]",
                "body": f"field(default=None, {field_meta('asdfg')})"
            },
            "dict": {
                "name": "dict",
                "type": "Dict[str, int]",
                "body": f"field({field_meta('dict')})"
            }
        },
        "generated": trim(f"""
        from dataclasses import dataclass, field
        from json_to_models.dynamic_typing import FloatString, IntString
        from typing import Dict, List, Optional


        @dataclass
        class Test:
            foo: int = field({field_meta('foo')})
            qwerty: FloatString = field({field_meta('qwerty')})
            dict: Dict[str, int] = field({field_meta('dict')})
            baz: Optional[List[List[str]]] = field(default_factory=list, {field_meta('baz')})
            bar: Optional[IntString] = field(default=None, {field_meta('bar')})
            asdfg: Optional[int] = field(default=None, {field_meta('asdfg')})
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
    gen = DataclassModelCodeGenerator(value, meta=True)
    required, optional = sort_fields(value)
    for is_optional, fields in enumerate((required, optional)):
        for field in fields:
            field_imports, data = gen.field_data(field, value.type[field], bool(is_optional))
            assert data == expected[field]


@pytest.mark.parametrize("value,expected", test_data_unzip["fields"])
def test_fields_attr(value: ModelMeta, expected: dict):
    expected_imports: str = expected["imports"]
    expected_fields: List[str] = expected["fields"]
    gen = DataclassModelCodeGenerator(value, meta=True)
    imports, fields = gen.fields
    imports = compile_imports(imports)
    assert imports == expected_imports
    assert fields == expected_fields


@pytest.mark.parametrize("value,expected", test_data_unzip["generated"])
def test_generated_attr(value: ModelMeta, expected: str):
    generated = generate_code(([{"model": value, "nested": []}], {}), DataclassModelCodeGenerator,
                              class_generator_kwargs={'meta': True})
    assert generated.rstrip() == expected, generated
