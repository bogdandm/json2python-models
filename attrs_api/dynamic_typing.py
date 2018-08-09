from typing import Union


class BaseType:
    pass


class UnknownType(BaseType):
    def __str__(self):
        return "Unknown"


Unknown = UnknownType()


class Single(BaseType):
    __slots__ = ["type"]

    def __init__(self, t: Union[type, BaseType]):
        self.type = t

    def __str__(self):
        return f"{self.__class__.__name__}[{self.type}]"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.type == other.type


class Many(BaseType):
    __slots__ = ["types"]

    def __init__(self, *types: Union[type, BaseType]):
        self.types = types

    def __str__(self):
        items = ', '.join(map(str, self.types))
        return f"{self.__class__.__name__}[{items}]"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and all(t1 == t2 for t1, t2 in zip(self.types, other.types))

    def __len__(self):
        return len(self.types)


class DOptional(Single):
    pass


class DUnion(Many):
    def __init__(self, *types: Union[type, BaseType]):
        unique_types = []
        for t in types:
            if t not in unique_types:
                unique_types.append(t)
        super().__init__(*unique_types)


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

NoneType = type(None)