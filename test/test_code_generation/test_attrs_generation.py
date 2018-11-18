from typing import Dict, List

import pytest

from json_to_models.dynamic_typing import (DDict, DList, DOptional, FloatString, IntString, ModelMeta, compile_imports)
from json_to_models.models import sort_fields
from json_to_models.models.attr import AttrsModelCodeGenerator, METADATA_FIELD_NAME, sort_kwargs
from json_to_models.models.base import generate_code
from test.test_code_generation.test_models_code_generator import model_factory, trim


def test_attrib_kwargs_sort():
    sorted_kwargs = sort_kwargs(dict(
        y=2,
        metadata='b',
        converter='a',
        default=None,
        x=1,
    ))
    expected = ['default', 'converter', 'y', 'x', 'metadata']
    for k1, k2 in zip(sorted_kwargs.keys(), expected):
        assert k1 == k2
    try:
        sort_kwargs({}, ['wrong_char'])
    except ValueError as e:
        assert e.args[0].endswith('wrong_char')
    else:
        assert 0, "XPass"



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
                "body": f"attr.ib({field_meta('foo')})"
            },
            "bar": {
                "name": "bar",
                "type": "int",
                "body": f"attr.ib({field_meta('bar')})"
            },
            "baz": {
                "name": "baz",
                "type": "float",
                "body": f"attr.ib({field_meta('baz')})"
            }
        },
        "fields": {
            "imports": "",
            "fields": [
                f"foo: int = attr.ib({field_meta('foo')})",
                f"bar: int = attr.ib({field_meta('bar')})",
                f"baz: float = attr.ib({field_meta('baz')})",
            ]
        },
        "generated": trim(f"""
        import attr
        
        
        @attr.s
        class Test:
            foo: int = attr.ib({field_meta('foo')})
            bar: int = attr.ib({field_meta('bar')})
            baz: float = attr.ib({field_meta('baz')})
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
                "body": f"attr.ib({field_meta('foo')})"
            },
            "baz": {
                "name": "baz",
                "type": "Optional[List[List[str]]]",
                "body": f"attr.ib(factory=list, {field_meta('baz')})"
            },
            "bar": {
                "name": "bar",
                "type": "Optional[IntString]",
                "body": f"attr.ib(default=None, converter=optional(IntString), {field_meta('bar')})"
            },
            "qwerty": {
                "name": "qwerty",
                "type": "FloatString",
                "body": f"attr.ib(converter=FloatString, {field_meta('qwerty')})"
            },
            "asdfg": {
                "name": "asdfg",
                "type": "Optional[int]",
                "body": f"attr.ib(default=None, {field_meta('asdfg')})"
            },
            "dict": {
                "name": "dict",
                "type": "Dict[str, int]",
                "body": f"attr.ib({field_meta('dict')})"
            }
        },
        "generated": trim(f"""
        import attr
        from attr.converter import optional
        from json_to_models.dynamic_typing import FloatString, IntString
        from typing import Dict, List, Optional


        @attr.s
        class Test:
            foo: int = attr.ib({field_meta('foo')})
            qwerty: FloatString = attr.ib(converter=FloatString, {field_meta('qwerty')})
            dict: Dict[str, int] = attr.ib({field_meta('dict')})
            baz: Optional[List[List[str]]] = attr.ib(factory=list, {field_meta('baz')})
            bar: Optional[IntString] = attr.ib(default=None, converter=optional(IntString), {field_meta('bar')})
            asdfg: Optional[int] = attr.ib(default=None, {field_meta('asdfg')})
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
    gen = AttrsModelCodeGenerator(value, meta=True)
    required, optional = sort_fields(value)
    for is_optional, fields in enumerate((required, optional)):
        for field in fields:
            field_imports, data = gen.field_data(field, value.type[field], bool(is_optional))
            assert data == expected[field]


@pytest.mark.parametrize("value,expected", test_data_unzip["fields"])
def test_fields_attr(value: ModelMeta, expected: dict):
    expected_imports: str = expected["imports"]
    expected_fields: List[str] = expected["fields"]
    gen = AttrsModelCodeGenerator(value, meta=True)
    imports, fields = gen.fields
    imports = compile_imports(imports)
    assert imports == expected_imports
    assert fields == expected_fields


@pytest.mark.parametrize("value,expected", test_data_unzip["generated"])
def test_generated_attr(value: ModelMeta, expected: str):
    generated = generate_code(([{"model": value, "nested": []}], {}), AttrsModelCodeGenerator,
                              class_generator_kwargs={'meta': True})
    assert generated.rstrip() == expected, generated
