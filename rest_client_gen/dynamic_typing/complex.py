from inspect import isclass
from typing import List, Optional, Tuple, Union

from .base import BaseType, ComplexType, MetaData, NoneType, SingleType


def _get_static_type(t: MetaData) -> MetaData:
    return t if isclass(t) or isinstance(t, dict) else t.to_static_type()


class DOptional(SingleType):
    """
    Field of this type may not be presented in JSON object
    """

    def to_static_type(self):
        return Optional[_get_static_type(self.type)]


class DUnion(ComplexType):
    """
    Same as typing.Union. Nested types are unique.
    """

    def __init__(self, *types: Union[type, BaseType, dict]):
        unique_types = []
        for t in types:
            if isinstance(t, DUnion):
                # Merging nested DUnions
                for t2 in list(t._extract_nested_types()):
                    if t2 not in unique_types:
                        unique_types.append(t2)
            elif t not in unique_types:
                # Ensure that types in union are unique
                unique_types.append(t)
        super().__init__(*unique_types)

    def _extract_nested_types(self):
        for t in self.types:
            if isinstance(t, DUnion):
                yield from t._extract_nested_types()
            else:
                yield t

    def to_static_type(self):
        optional = NoneType in self.types
        t = tuple(_get_static_type(t) for t in self if t is not NoneType)
        res = Union[t]
        if optional:
            res = Optional[res]
        return res


class DTuple(ComplexType):
    def to_static_type(self):
        return Tuple[tuple(_get_static_type(t) for t in self)]


class DList(SingleType):
    def to_static_type(self):
        return List[_get_static_type(self.type)]
