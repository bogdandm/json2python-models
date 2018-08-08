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
