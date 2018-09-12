from inspect import isclass
from typing import Iterable, List, Tuple, Union

ImportPath = List[Tuple[str, Union[Iterable[str], str]]]


class BaseType:
    def __iter__(self) -> Iterable['MetaData']:
        raise NotImplementedError()

    def replace(self, t: Union['MetaData', List['MetaData']], **kwargs) -> 'BaseType':
        """
        Replace nested type in-place

        :param t: Meta type
        :param kwargs: Other args
        :return:
        """
        raise NotImplementedError()

    def to_typing_code(self) -> Tuple[ImportPath, str]:
        """
        Return typing code that represents this metadata and import path of classes that are used in this code

        :return: ((module_name, (class_name, ...)), code)
        """
        raise NotImplementedError()


class UnknownType(BaseType):
    __slots__ = []

    def __str__(self):
        return "Unknown"

    def __iter__(self) -> Iterable['MetaData']:
        return ()

    def replace(self, t: 'MetaData', **kwargs) -> 'UnknownType':
        return self

    def to_typing_code(self) -> Tuple[ImportPath, str]:
        return ([('typing', 'Any')], 'Any')


Unknown = UnknownType()
NoneType = type(None)
MetaData = Union[type, dict, BaseType]


class SingleType(BaseType):
    __slots__ = ["type"]

    def __init__(self, t: MetaData):
        self.type = t

    def __str__(self):
        return f"{self.__class__.__name__}[{self.type}]"

    def __repr__(self):
        return f"<{self.__class__.__name__} [{self.type}]>"

    def __iter__(self) -> Iterable['MetaData']:
        yield self.type

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.type == other.type

    def replace(self, t: 'MetaData', **kwargs) -> 'SingleType':
        self.type = t
        return self


class ComplexType(BaseType):
    __slots__ = ["_types"]

    def __init__(self, *types: MetaData):
        self._types = list(types)

    @property
    def types(self):
        return self._types

    @types.setter
    def types(self, value):
        self._types = value
        self._sorted = None

    @property
    def sorted(self):
        """
        Getter of cached sorted types list
        """
        sorted_types = getattr(self, '_sorted', None)
        if sorted_types is None:
            sorted_types = sorted(self.types, key=self._sort_key)
            self._sorted = sorted_types
        return sorted_types

    def _sort_key(self, item):
        if hasattr(item, 'keys'):
            return str(sorted(item.keys()))
        else:
            return str(item)

    def __str__(self):
        items = ', '.join(map(str, self.types))
        return f"{self.__class__.__name__}[{items}]"

    def __repr__(self):
        items = ', '.join(map(str, self.types))
        return f"<{self.__class__.__name__} [{items}]>"

    def __iter__(self) -> Iterable['MetaData']:
        yield from self.types

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.sorted == other.sorted

    def __len__(self):
        return len(self.types)

    def replace(self, t: Union['MetaData', List['MetaData']], index=None, **kwargs) -> 'ComplexType':
        if index is None and isinstance(t, list):
            self.types = t
        elif index is not None and not isinstance(t, list):
            types = self.types
            types[index] = t
            # Using property setter here
            self.types = types
        else:
            raise ValueError(f"Unsupported arguments: t={t} index={index} kwargs={kwargs}")
        return self

    def to_typing_code(self) -> Tuple[ImportPath, str]:
        imports, nested = zip(*map(metadata_to_typing, self))
        nested = ", ".join(nested)
        return (
            imports,
            f"[{nested}]"
        )


def metadata_to_typing(t: MetaData) -> Tuple[ImportPath, str]:
    if isclass(t):
        return ([], t.__name__)
    elif isinstance(t, dict):
        raise ValueError("Can not convert dict instance to typing code. It should be wrapped into ModelMeta instance")
    return t.to_typing_code()
