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


# TODO: rewrite into pytest
print(r.resolve(A, B))
print(r.resolve(A, B, C))
print(r.resolve(A, B, D))
print(r.resolve(X, B))
