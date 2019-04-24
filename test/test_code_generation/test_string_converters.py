from typing import Dict, List, Optional

import attr

from json_to_models.dynamic_typing import FloatString, IntString
from json_to_models.models import ClassType
from json_to_models.models.string_converters import convert_strings, post_init_converters


def test_post_init_converters():
    from dataclasses import dataclass

    @dataclass
    class A:
        x: IntString
        y: FloatString

        __post_init__ = post_init_converters(['x', 'y'])

    a = A('1', '1.1')
    assert type(a.x) is IntString
    assert type(a.y) is FloatString

    @attr.s
    class A:
        x: IntString = attr.ib()
        y: FloatString = attr.ib()

        __attrs_post_init__ = post_init_converters(['x', 'y'])

    a = A('1', '1.1')
    assert type(a.x) is IntString
    assert type(a.y) is FloatString


def test_convert_strings_decorator():
    from dataclasses import dataclass

    @dataclass
    @convert_strings(['x', 'y'], class_type=ClassType.Dataclass)
    class A:
        x: IntString
        y: FloatString

    @dataclass
    @convert_strings(['x', 'y'], class_type=ClassType.Dataclass)
    class B:
        x: IntString
        y: FloatString

        def __post_init__(self):
            self.x *= 2

    a = A('1', '1.1')
    b = B('1', '1.1')
    assert type(a.x) is IntString
    assert type(a.y) is FloatString
    assert b.x == 2


def test_convert_complex_data():
    from dataclasses import dataclass

    @dataclass
    @convert_strings(['x', 'y#L.S', 'z#D.S', 'a#O.S', 'b#O.L.D.L.S'], class_type=ClassType.Dataclass)
    class A:
        x: IntString
        y: List[IntString]
        z: Dict[str, IntString]
        a: Optional[IntString]
        b: Optional[List[Dict[str, List[IntString]]]]

    a = A('1', '1234', {'s': '2', 'w': '3'}, None,
          [{'a': ['1', '2']}, {'b': ['3', '2']}])

    assert a == A(1, [1, 2, 3, 4], {'s': 2, 'w': 3}, None,
                  [{'a': [1, 2]}, {'b': [3, 2]}])

    @attr.s
    @convert_strings(['x', 'y#L.S', 'z#D.S', 'a#O.S', 'b#O.L.D.L.S'], class_type=ClassType.Attrs)
    class A:
        x: IntString = attr.ib()
        y: List[IntString] = attr.ib()
        z: Dict[str, IntString] = attr.ib()
        a: Optional[IntString] = attr.ib(default=None)
        b: Optional[List[Dict[str, List[IntString]]]] = attr.ib(default=None)

    a = A('1', '1234', {'s': '2', 'w': '3'}, None,
          [{'a': ['1', '2']}, {'b': ['3', '2']}])

    assert a == A(1, [1, 2, 3, 4], {'s': 2, 'w': 3}, None,
                  [{'a': [1, 2]}, {'b': [3, 2]}])
