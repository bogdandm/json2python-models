from typing import Dict, List

import pytest

from json_to_models.dynamic_typing import (AbsoluteModelRef, DDict, DList, DOptional, IntString, ModelMeta, ModelPtr,
                                           Unknown, compile_imports)
from json_to_models.models.base import GenericModelCodeGenerator, generate_code
from json_to_models.models.structure import sort_fields
from json_to_models.models.utils import indent

# Data structure:
# (string, indent lvl, indent string)
# result
test_indent_data = [
    pytest.param(
        ("1", 1, " " * 4),
        "    1"
    ),
    pytest.param(
        ("1\n2", 1, " " * 4),
        "    1\n    2"
    ),
    pytest.param(
        ("1\n2", 2, " " * 4),
        "        1\n        2"
    ),
    pytest.param(
        ("1\n    2", 2, " " * 4),
        "        1\n            2"
    ),
]


@pytest.mark.parametrize("args,expected", test_indent_data)
def test_indent(args, expected):
    assert indent(*args) == expected


def model_factory(name: str, metadata: dict):
    model = ModelMeta(metadata, name)
    model.set_raw_name(name)
    return model


INDENT = " " * 4 * 2


def trim(s: str):
    if "\n" in s:
        n = len(INDENT)
        lines = s.split("\n")
        for i in (0, -1):
            if not lines[i].strip():
                del lines[i]

        s = "\n".join(line[n:] if line[:n] == INDENT else line for line in lines)
    return s


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
                "type": "int"
            },
            "bar": {
                "name": "bar",
                "type": "int"
            },
            "baz": {
                "name": "baz",
                "type": "float"
            }
        },
        "fields": {
            "imports": "",
            "fields": [
                "foo: int",
                "bar: int",
                "baz: float",
            ]
        },
        "generated": trim("""
        class Test:
            foo: int
            bar: int
            baz: float
        """)
    },
    "complex": {
        "model": ("Test", {
            "foo": int,
            "baz": DOptional(DList(DList(str))),
            "bar": IntString,
            "d": DDict(Unknown)
        }),
        "fields_data": {
            "foo": {
                "name": "foo",
                "type": "int"
            },
            "baz": {
                "name": "baz",
                "type": "Optional[List[List[str]]]"
            },
            "bar": {
                "name": "bar",
                "type": "IntString"
            },
            "d": {
                "name": "d",
                "type": "Dict[str, Any]"
            }
        },
        "fields": {
            "imports": "from json_to_models.dynamic_typing import IntString\n"
                       "from typing import Any, Dict, List, Optional",
            "fields": [
                "foo: int",
                "bar: IntString",
                "d: Dict[str, Any]",
                "baz: Optional[List[List[str]]]",
            ]
        },
        "generated": trim("""
        from json_to_models.dynamic_typing import IntString
        from typing import Any, Dict, List, Optional
        
        
        class Test:
            foo: int
            bar: IntString
            d: Dict[str, Any]
            baz: Optional[List[List[str]]]
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
def test_fields_data(value: ModelMeta, expected: Dict[str, dict]):
    gen = GenericModelCodeGenerator(value)
    required, optional = sort_fields(value)
    for is_optional, fields in enumerate((required, optional)):
        for field in fields:
            field_imports, data = gen.field_data(field, value.type[field], bool(is_optional))
            assert data == expected[field]


@pytest.mark.parametrize("value,expected", test_data_unzip["fields"])
def test_fields(value: ModelMeta, expected: dict):
    expected_imports: str = expected["imports"]
    expected_fields: List[str] = expected["fields"]
    gen = GenericModelCodeGenerator(value)
    imports, fields = gen.fields
    imports = compile_imports(imports)
    assert imports == expected_imports
    assert fields == expected_fields


@pytest.mark.parametrize("value,expected", test_data_unzip["generated"])
def test_generated(value: ModelMeta, expected: str):
    generated = generate_code(([{"model": value, "nested": []}], {}), GenericModelCodeGenerator)
    assert generated.rstrip() == expected, generated


def test_absolute_model_ref():
    test_model = ModelMeta({"field": int}, "A")
    test_model.name = "test_model"
    test_ptr = ModelPtr(test_model)
    assert test_ptr.to_typing_code()[1] == "'TestModel'"
    with AbsoluteModelRef.inject({test_model: "Parent"}):
        assert test_ptr.to_typing_code()[1] == "'Parent.TestModel'"
    assert test_ptr.to_typing_code()[1] == "'TestModel'"
    with AbsoluteModelRef.inject({test_model: "Parent"}):
        assert test_ptr.to_typing_code()[1] == "'Parent.TestModel'"
        with AbsoluteModelRef.inject({test_model: "AnotherParent"}):
            assert test_ptr.to_typing_code()[1] == "'AnotherParent.TestModel'"
        assert test_ptr.to_typing_code()[1] == "'Parent.TestModel'"

    wrapper = DList(DList(test_ptr))
    assert wrapper.to_typing_code()[1] == "List[List['TestModel']]"
    with AbsoluteModelRef.inject({test_model: test_model}):
        assert wrapper.to_typing_code()[1] == "List[List['TestModel.TestModel']]"
