from inspect import isclass
from typing import Optional, Union, Tuple, List

from .base import SingleType, ComplexType, BaseType


class DOptional(SingleType):
    def to_static_type(self):
        return Optional[self.type if isclass(self.type) else self.type.to_static_type()]


class DUnion(ComplexType):
    def __init__(self, *types: Union[type, BaseType]):
        unique_types = []
        for t in types:
            if t not in unique_types:
                unique_types.append(t)
        super().__init__(*unique_types)

    def to_static_type(self):
        t = tuple(t if isclass(t) else t.to_static_type() for t in self.types)
        return Union[t]


class DTuple(ComplexType):
    def to_static_type(self):
        t = tuple(t if isclass(t) else t.to_static_type() for t in self.types)
        return Tuple[t]


class DList(SingleType):
    def to_static_type(self):
        return List[self.type if isclass(self.type) else self.type.to_static_type()]