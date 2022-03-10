import json
from functools import partial
from itertools import chain
from typing import AbstractSet, Dict, Iterable, List, Optional, Tuple, Type, Union

from typing_extensions import Literal

from .base import BaseType, ImportPathList, MetaData, get_hash_string
from .typing import metadata_to_typing


class SingleType(BaseType):
    _typing_cls = None
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

    def to_typing_code(self, types_style: Dict[Union['BaseType', Type['BaseType']], dict]) \
            -> Tuple[ImportPathList, str]:
        imports, nested = metadata_to_typing(self.type, types_style=types_style)
        return (
            [*imports, (self._typing_cls.__module__, self._typing_cls._name)],
            f"{self._typing_cls._name}[{nested}]"
        )

    def _to_hash_string(self) -> str:
        return f"{type(self).__name__}/{get_hash_string(self.type)}"


class ComplexType(BaseType):
    _typing_cls = None
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

    def to_typing_code(self, types_style: Dict[Union['BaseType', Type['BaseType']], dict]) \
            -> Tuple[ImportPathList, str]:
        imports, nested = zip(*map(partial(metadata_to_typing, types_style=types_style), self))
        nested = ", ".join(nested)
        return (
            [*chain.from_iterable(imports), (self._typing_cls.__module__, self._typing_cls._name)],
            f"{self._typing_cls._name}[{nested}]"
        )

    def _to_hash_string(self) -> str:
        return type(self).__name__ + "/" + ",".join(map(get_hash_string, self.types))


class DOptional(SingleType):
    """
    Field of this type may not be presented in JSON object
    """
    _typing_cls = Optional


class DUnion(ComplexType):
    """
    Same as typing.Union. Nested types are unique.
    """
    _typing_cls = Union

    def __init__(self, *types: Union[type, BaseType, dict]):
        hashes = set()
        unique_types = []
        use_literals = True
        str_literals = set()

        # Ensure that types in union are unique

        def handle_type(t, use_literals):
            if t is str:
                use_literals = False

            if isinstance(t, StringLiteral):
                if not use_literals:
                    return

                if t.overflowed:
                    use_literals = False
                else:
                    str_literals.update(t.literals)

            else:
                h = get_hash_string(t)
                if h not in hashes:
                    unique_types.append(t)
                    hashes.add(h)
            return use_literals

        for t in types:
            if isinstance(t, DUnion):
                # Merging nested DUnions
                for t2 in list(t._extract_nested_types()):
                    use_literals = handle_type(t2, use_literals) and use_literals
            else:
                use_literals = handle_type(t, use_literals) and use_literals

        if str_literals and use_literals:
            literal = StringLiteral(str_literals)
            if literal.overflowed:
                use_literals = False
            else:
                unique_types.append(literal)

        if not use_literals:
            handle_type(str, use_literals=False)
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


class DTuple(ComplexType):
    _typing_cls = Tuple


class DList(SingleType):
    _typing_cls = List


class DDict(SingleType):
    _typing_cls = Dict

    # Dict is single type because keys of JSON dict are always strings.
    def to_typing_code(self, types_style: Dict[Union['BaseType', Type['BaseType']], dict]) \
            -> Tuple[ImportPathList, str]:
        imports, nested = metadata_to_typing(self.type, types_style=types_style)
        return (
            [*imports, ('typing', 'Dict')],
            f"Dict[str, {nested}]"
        )


class StringLiteral(BaseType):
    class TypeStyle:
        use_literals = 'use_literals'
        max_literals = 'max_literals'

    MAX_LITERALS = 15  # Hard limit for performance optimization
    MAX_STRING_LENGTH = 20
    __slots__ = ["_literals", "_hash", "_overflow"]

    def __init__(self, literals: AbstractSet[str]):
        self._overflow = (
                len(literals) > self.MAX_LITERALS
                or
                any(map(
                    lambda s: len(s) >= self.MAX_STRING_LENGTH,
                    literals
                ))
        )
        self._literals = frozenset() if self._overflow else literals

    def __iter__(self) -> Iterable['MetaData']:
        return iter(())

    def __str__(self):
        return f"{type(self).__name__}[{self._repr_literals()}]"

    def __repr__(self):
        return f"<{type(self).__name__} [{self._repr_literals()}]>"

    def __eq__(self, other):
        return type(other) is type(self) and self._literals == other._literals

    def replace(self, t: 'MetaData', **kwargs) -> 'StringLiteral':
        return self

    def to_typing_code(self, types_style: Dict[Union['BaseType', Type['BaseType']], dict]) \
            -> Tuple[ImportPathList, str]:
        options = self.get_options_for_type(self, types_style)
        if options.get(self.TypeStyle.use_literals):
            limit = options.get(self.TypeStyle.max_literals)
            if limit is None or len(self.literals) < limit:
                parts = ', '.join(
                    json.dumps(s)
                    for s in sorted(self.literals)
                )
                return [(Literal.__module__, 'Literal')], f"Literal[{parts}]"

        return [], 'str'

    def _to_hash_string(self) -> str:
        return f"{type(self).__name__}/{self._repr_literals()}"

    @property
    def literals(self):
        return self._literals

    @property
    def overflowed(self):
        return self._overflow

    def _repr_literals(self):
        if self._overflow:
            return '...'
        return ','.join(self._literals)
