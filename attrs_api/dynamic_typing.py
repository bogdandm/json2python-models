from typing import Union


class BaseType:
    pass


class Single(BaseType):
    __slots__ = ["type"]

    def __init__(self, t: Union[type, BaseType]):
        self.type = t

    def __str__(self):
        return f"{self.__class__.__name__}[{self.type}]"


class Many(BaseType):
    __slots__ = ["types"]

    def __init__(self, *types: Union[type, BaseType]):
        self.types = types

    def __str__(self):
        items = ', '.join(map(str, self.types))
        return f"{self.__class__.__name__}[{items}]"


class DOptional(Single):
    pass


class DUnion(Many):
    pass


class DTuple(Many):
    pass


class DList(Single):
    pass


class StringSerializable(BaseType):
    @classmethod
    def to_internal_value(cls, value: str) -> 'StringSerializable':
        raise NotImplementedError()

    def to_representation(self) -> str:
        raise NotImplementedError()


class IntString(StringSerializable, int):
    @classmethod
    def to_internal_value(cls, value: str) -> 'IntString':
        return cls(value)

    def to_representation(self) -> str:
        raise str(self)


class FloatString(StringSerializable, float):
    @classmethod
    def to_internal_value(cls, value: str) -> 'FloatString':
        return cls(value)

    def to_representation(self) -> str:
        raise str(self)


class BooleanString(StringSerializable, int):
    # We can't extend bool class, but we can extend int with same result excepting isinstance and issubclass check

    @classmethod
    def to_internal_value(cls, value: str) -> 'BooleanString':
        b = {"true": True, "false": False}.get(value.lower(), None)
        if b is None:
            raise ValueError(f"invalid literal for bool: '{value}'")
        return cls(b)

    def to_representation(self) -> str:
        raise str(bool(self)).lower()


STRING_CONVERTERS = (IntString, FloatString, BooleanString)
