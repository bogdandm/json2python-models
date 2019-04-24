from typing import Dict, List

import pytest

from json_to_models.dynamic_typing import (DDict, DList, DOptional, DUnion, FloatString, IntString, ModelMeta,
                                           compile_imports)
from json_to_models.models.attr import AttrsModelCodeGenerator, DEFAULT_ORDER
from json_to_models.models.base import METADATA_FIELD_NAME, generate_code, sort_kwargs
from json_to_models.models.structure import sort_fields
from test.test_code_generation.test_models_code_generator import model_factory, trim


def test_attrib_kwargs_sort():
    sorted_kwargs = sort_kwargs(dict(
        y=2,
        metadata='b',
        converter='a',
        default=None,
        x=1,
    ), DEFAULT_ORDER)
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
            "Bar": int,
            "baz": float
        }),
        "fields_data": {
            "foo": {
                "name": "foo",
                "type": "int",
                "body": f"attr.ib()"
            },
            "Bar": {
                "name": "bar",
                "type": "int",
                "body": f"attr.ib({field_meta('Bar')})"
            },
            "baz": {
                "name": "baz",
                "type": "float",
                "body": f"attr.ib()"
            }
        },
        "fields": {
            "imports": "",
            "fields": [
                f"foo: int = attr.ib()",
                f"bar: int = attr.ib({field_meta('Bar')})",
                f"baz: float = attr.ib()",
            ]
        },
        "generated": trim(f"""
        import attr
        
        
        @attr.s
        class Test:
            foo: int = attr.ib()
            bar: int = attr.ib({field_meta('Bar')})
            baz: float = attr.ib()
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
                "type": "int",
                "body": "attr.ib()"
            },
            "baz": {
                "name": "baz",
                "type": "Optional[List[List[str]]]",
                "body": "attr.ib(factory=list)"
            },
            "bar": {
                "name": "bar",
                "type": "Optional[IntString]",
                "body": "attr.ib(default=None, converter=optional(IntString))"
            },
            "qwerty": {
                "name": "qwerty",
                "type": "FloatString",
                "body": "attr.ib(converter=FloatString)"
            },
            "asdfg": {
                "name": "asdfg",
                "type": "Optional[int]",
                "body": "attr.ib(default=None)"
            },
            "dict": {
                "name": "dict",
                "type": "Dict[str, int]",
                "body": "attr.ib()"
            },
            "not": {
                "name": "not_",
                "type": "bool",
                "body": f"attr.ib({field_meta('not')})"
            },
            "1day": {
                "name": "one_day",
                "type": "int",
                "body": f"attr.ib({field_meta('1day')})"
            },
            "день_недели": {
                "name": "den_nedeli",
                "type": "str",
                "body": f"attr.ib({field_meta('день_недели')})"
            }
        },
        "generated": trim(f"""
        import attr
        from json_to_models.dynamic_typing import FloatString, IntString
        from json_to_models.models import ClassType
        from json_to_models.models.string_converters import convert_strings
        from typing import Dict, List, Optional


        @attr.s
        @convert_strings(['bar#O.S', 'qwerty'], class_type=ClassType.Attrs)
        class Test:
            foo: int = attr.ib()
            qwerty: FloatString = attr.ib()
            dict: Dict[str, int] = attr.ib()
            not_: bool = attr.ib({field_meta('not')})
            one_day: int = attr.ib({field_meta('1day')})
            den_nedeli: str = attr.ib({field_meta('день_недели')})
            baz: Optional[List[List[str]]] = attr.ib(factory=list)
            bar: Optional[IntString] = attr.ib(default=None)
            asdfg: Optional[int] = attr.ib(default=None)
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
        import attr
        from json_to_models.dynamic_typing import FloatString, IntString
        from json_to_models.models import ClassType
        from json_to_models.models.string_converters import convert_strings
        from typing import Dict, List, Optional, Union


        @attr.s
        @convert_strings(['b', 'c#O.S', 'd#L.L.L.S', 'e#D.S'], class_type=ClassType.Attrs)
        class Test:
            a: int = attr.ib()
            b: IntString = attr.ib()
            d: List[List[List[IntString]]] = attr.ib()
            e: Dict[str, IntString] = attr.ib()
            u: Union[Dict[str, IntString], List[List[IntString]]] = attr.ib()
            c: Optional[FloatString] = attr.ib(default=None)
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
                              class_generator_kwargs={'meta': True, 'post_init_converters': True})
    assert generated.rstrip() == expected, generated
