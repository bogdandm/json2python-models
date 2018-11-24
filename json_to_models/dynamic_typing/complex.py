from itertools import chain
from typing import Iterable, List, Tuple, Union

from .base import BaseType, ImportPathList, MetaData, get_hash_string
from .typing import metadata_to_typing


class SingleType(BaseType):
    __slots__ = ["_type", "_hash"]

    def __init__(self, t: MetaData):
        self._type = t
        self._hash = None

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, t: MetaData):
        self._type = t
        self._hash = None

    def __str__(self):
        return f"{type(self).__name__}[{self.type}]"

    def __repr__(self):
        return f"<{type(self).__name__} [{self.type}]>"

    def __iter__(self) -> Iterable['MetaData']:
        yield self.type

    def __eq__(self, other):
        return type(other) is type(self) and self.type == other.type

    def replace(self, t: 'MetaData', **kwargs) -> 'SingleType':
        self.type = t
        return self

    def _to_hash_string(self) -> str:
        return f"{type(self).__name__}/{get_hash_string(self.type)}"


class ComplexType(BaseType):
    __slots__ = ["_types", "_sorted", "_hash"]

    def __init__(self, *types: MetaData):
        self._types = list(types)
        self._sorted = None
        self._hash = None

    @property
    def types(self):
        return self._types

    @types.setter
    def types(self, value):
        self._types = value
        self._sorted = None
        self._hash = None

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

    @staticmethod
    def _sort_key(item):
        if hasattr(item, 'keys'):
            return str(sorted(item.keys()))
        else:
            return str(item)

    def __str__(self):
        items = ', '.join(map(str, self.types))
        return f"{type(self).__name__}[{items}]"

    def __repr__(self):
        items = ', '.join(map(str, self.types))
        return f"<{type(self).__name__} [{items}]>"

    def __iter__(self) -> Iterable['MetaData']:
        yield from self.types

    def __eq__(self, other):
        return type(other) is type(self) and self.sorted == other.sorted

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

    def to_typing_code(self) -> Tuple[ImportPathList, str]:
        imports, nested = zip(*map(metadata_to_typing, self))
        nested = ", ".join(nested)
        return (
            list(chain(*imports)),
            f"[{nested}]"
        )

    def _to_hash_string(self) -> str:
        return type(self).__name__ + "/" + ",".join(map(get_hash_string, self.types))


class DOptional(SingleType):
    """
    Field of this type may not be presented in JSON object
    """

    def to_typing_code(self) -> Tuple[ImportPathList, str]:
        imports, nested = metadata_to_typing(self.type)
        return (
            [*imports, ('typing', 'Optional')],
            f"Optional[{nested}]"
        )


class DUnion(ComplexType):
    """
    Same as typing.Union. Nested types are unique.
    """

    def __init__(self, *types: Union[type, BaseType, dict]):
        hashes = set()
        unique_types = []
        # Ensure that types in union are unique
        for t in types:
            if isinstance(t, DUnion):
                # Merging nested DUnions
                for t2 in list(t._extract_nested_types()):
                    h = get_hash_string(t2)
                    if h not in hashes:
                        unique_types.append(t2)
                        hashes.add(h)
            else:
                h = get_hash_string(t)
                if h not in hashes:
                    unique_types.append(t)
                    hashes.add(h)
        super().__init__(*unique_types)

    def _extract_nested_types(self):
        """
        Same as ComplexType.__iter__ but "flatten" nested DUnions
        """
        for t in self.types:
            if isinstance(t, DUnion):
                yield from t._extract_nested_types()
            else:
                yield t

    def to_typing_code(self) -> Tuple[ImportPathList, str]:
        imports, nested = super().to_typing_code()
        return (
            [*imports, ('typing', 'Union')],
            "Union" + nested
        )


class DTuple(ComplexType):
    def to_typing_code(self) -> Tuple[ImportPathList, str]:
        imports, nested = super().to_typing_code()
        return (
            [*imports, ('typing', 'Tuple')],
            "Tuple" + nested
        )


class DList(SingleType):
    def to_typing_code(self) -> Tuple[ImportPathList, str]:
        imports, nested = metadata_to_typing(self.type)
        return (
            [*imports, ('typing', 'List')],
            f"List[{nested}]"
        )


class DDict(SingleType):
    # Dict is single type because keys of JSON dict are always strings.
    def to_typing_code(self) -> Tuple[ImportPathList, str]:
        imports, nested = metadata_to_typing(self.type)
        return (
            [*imports, ('typing', 'Dict')],
            f"Dict[str, {nested}]"
        )
