import pytest

from rest_client_gen.dynamic_typing.string_serializable import StringSerializable, StringSerializableRegistry

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


print(r.resolve(A, B))
print(r.resolve(A, B, C))
print(r.resolve(A, B, D))
print(r.resolve(X, B))

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