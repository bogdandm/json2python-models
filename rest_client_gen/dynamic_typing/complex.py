from typing import Union

from .base import BaseType, ComplexType, SingleType


class DOptional(SingleType):
    """
    Field of this type may not be presented in JSON object
    """
    pass


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


class DTuple(ComplexType):
    pass


class DList(SingleType):
    pass
