import pytest

from rest_client_gen.dynamic_typing import IsoTimeString
from rest_client_gen.dynamic_typing.string_serializable import (FloatString, IntString, StringSerializable,
                                                                StringSerializableRegistry)
from rest_client_gen.generator import MetadataGenerator

r = StringSerializableRegistry()


@r.add()
class A(StringSerializable):
    pass


@r.add({A})
class D(StringSerializable):
    pass


@r.add({D, A})
class E(StringSerializable):
    pass


@r.add({A, E, D})
class B(StringSerializable):
    pass


@r.add({B, A, E, D})
class C(StringSerializable):
    pass


@r.add({C, B, A, E, D})
class F(StringSerializable):
    pass


@r.add({A})
class X(StringSerializable):
    pass


@r.add({X})
class Y(StringSerializable):
    pass


# resolve args | resolved nodes
test_data = [
    pytest.param((A, B), {B}),
    pytest.param((A, B, C), {C}),
    pytest.param((B, B), {B}),
    pytest.param((A, B, D), {B}),
    pytest.param((X, B), {B, X}),
]


@pytest.mark.parametrize("value,expected", test_data)
def test_string_serializable_registry(value, expected):
    result = r.resolve(*value)
    assert result == expected


r2 = StringSerializableRegistry()
gen = MetadataGenerator(r2)

r2.add(cls=IsoTimeString)
r2.add(cls=IntString)
r2.add(replace_types=(IntString,), cls=FloatString)


@pytest.mark.xfail()
def test_without_remove():
    assert gen._detect_type("12") == IntString


r2.remove(IsoTimeString)
r2.add(cls=IsoTimeString)


def test_remove():
    assert gen._detect_type("12") == IntString
    assert gen._detect_type("12:14") == IsoTimeString
