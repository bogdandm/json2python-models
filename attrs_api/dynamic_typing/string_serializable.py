from .base import BaseType


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