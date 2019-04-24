from itertools import permutations
from typing import Collection, Iterable, List, Set, Tuple, Type

from .base import BaseType, ImportPathList


class StringSerializable(BaseType):
    """
    Mixin for classes which are used to (de-)serialize some values in a string form
    """

    @classmethod
    def to_internal_value(cls, value: str) -> 'StringSerializable':
        """
        Factory method

        :raises ValueError: if this class can not represent given value
        :param value: some string literal
        :return: Instance of this class
        """
        raise NotImplementedError()

    def to_representation(self) -> str:
        """
        Convert instance to string literal

        :return: string literal
        """
        raise NotImplementedError()

    @classmethod
    def to_typing_code(cls) -> Tuple[ImportPathList, str]:
        """
        Unlike other BaseType's subclasses it's a class method because StringSerializable instance is not parameterized
        as a metadata instance but contains actual data
        """
        cls_name = cls.__name__
        return [('json_to_models.dynamic_typing', cls_name)], cls_name

    def __iter__(self):
        return iter(())


T_StringSerializable = Type[StringSerializable]


class StringSerializableRegistry:
    def __init__(self, *types: T_StringSerializable):
        self.types: List[T_StringSerializable] = list(types)
        self.replaces: Set[Tuple[T_StringSerializable, T_StringSerializable]] = set()

    def __iter__(self):
        return iter(self.types)

    def __contains__(self, item):
        return item in self.types

    def add(self, replace_types: Iterable[T_StringSerializable] = (), cls: type = None):
        """
        Register decorated class in registry. Can be called as a method if cls argument is passed.

        :param replace_types: List of classes that is the particular case of decorated one
        :param cls: StringSerializable class
        :return: decorator
        """

        def decorator(cls):
            self.types.append(cls)
            for t in replace_types:
                self.replaces.add((t, cls))
            return cls

        if cls:
            decorator(cls)
            return

        return decorator

    def remove(self, cls: type):
        """
        Unregister given class

        :param cls: StringSerializable class
        """
        self.types.remove(cls)
        for base, replace in list(self.replaces):
            if replace is cls or base is cls:
                self.replaces.remove((base, replace))

    def resolve(self, *types: T_StringSerializable) -> Collection[T_StringSerializable]:
        """
        Return set of StringSerializable classes which can represent all classes from types argument.

        :param types: Sequence of StringSerializable classes
        :return: Set of StringSerializable
        """
        # TODO: Resolve common type of 2 different types (e.g str from float and bool)
        # Do it by getting all childs of each class with their level then merge it into one list and find one with min(max(levels) for c n childs)
        types = set(types)
        flag = True
        while flag:
            flag = False
            filtered: Set[T_StringSerializable] = set()
            for t1, t2 in permutations(types, 2):
                if (t1, t2) in self.replaces:
                    filtered.add(t2)
                    flag = True
            if flag:
                types = filtered
        # noinspection PyUnboundLocalVariable
        return types


# Default registry
registry = StringSerializableRegistry()


@registry.add()
class IntString(StringSerializable, int):
    @classmethod
    def to_internal_value(cls, value: str) -> 'IntString':
        return cls(value)

    def to_representation(self) -> str:
        return str(self)


@registry.add(replace_types=(IntString,))
class FloatString(StringSerializable, float):
    @classmethod
    def to_internal_value(cls, value: str) -> 'FloatString':
        return cls(value)

    def to_representation(self) -> str:
        return str(self)


@registry.add()
class BooleanString(StringSerializable, int):
    # We can't extend bool class, but we can extend int with same result excepting isinstance and issubclass check

    @classmethod
    def to_internal_value(cls, value: str) -> 'BooleanString':
        b = {"true": True, "false": False}.get(value.lower(), None)
        if b is None:
            raise ValueError(f"invalid literal for bool: '{value}'")
        return cls(b)

    def to_representation(self) -> str:
        return str(bool(self)).lower()
