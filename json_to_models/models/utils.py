from collections import defaultdict
from typing import Generic, TypeVar, Union

from . import INDENT

T = TypeVar('T')


class ListEx(list, Generic[T]):
    """
    Extended list with shortcut methods
    """

    def safe_index(self, value: T):
        try:
            return self.index(value)
        except ValueError:
            return None

    def _safe_indexes(self, *values: T):
        return [i for i in map(self.safe_index, values) if i is not None]

    def insert_before(self, value: T, *before: T):
        ix = self._safe_indexes(*before)
        if not ix:
            raise ValueError
        pos = min(ix)
        self.insert(pos, value)
        return pos

    def insert_after(self, value: T, *after: T):
        ix = self._safe_indexes(*after)
        if not ix:
            raise ValueError
        pos = max(ix) + 1
        self.insert(pos, value)
        return pos


class PositionsDict(defaultdict):
    # Dict contains mapping Index -> position, where position is list index to insert nested element of Index
    INC = object()

    def __init__(self, default_factory=int, **kwargs):
        super().__init__(default_factory, **kwargs)

    def update_position(self, key: str, value: Union[object, int]):
        """
        Shift all elements which are placed after updated one

        :param key: Index or "root"
        :param value: Could be position or PositionsDict.INC to perform quick increment (x+=1)
        :return:
        """
        if value is self.INC:
            value = self[key] + 1
        if key in self:
            old_value = self[key]
            delta = value - old_value
        else:
            old_value = value
            delta = 1
        for k, v in self.items():
            if k != key and v >= old_value:
                self[k] += delta
        self[key] = value


def indent(string: str, lvl: int = 1, indent: str = INDENT) -> str:
    """
    Indent all lines of string by ``indent * lvl``
    """
    return "\n".join(indent * lvl + line for line in string.split("\n"))
