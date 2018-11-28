from inspect import isclass
from typing import Iterable, List, Tuple, Union

ImportPathList = List[Tuple[str, Union[Iterable[str], str, None]]]


class BaseType:
    def __iter__(self) -> Iterable['MetaData']:
        """
        Yields nested metadata items
        """
        raise NotImplementedError()

    def replace(self, t: Union['MetaData', List['MetaData']], **kwargs) -> 'BaseType':
        """
        Replace nested type in-place

        :param t: Meta type
        :param kwargs: Other args
        :return:
        """
        raise NotImplementedError()

    def to_typing_code(self) -> Tuple[ImportPathList, str]:
        """
        Return typing code that represents this metadata and import path of classes that are used in this code

        :return: ((module_name, (class_name, ...)), code)
        """
        raise NotImplementedError()

    def to_hash_string(self) -> str:
        """
        Return unique string that can be used to generate hash of type instance.
        Caches hash value by default. If subclass can mutate (by default it always can)
        then it should define setters to safely invalidate cached value.

        :return: hash string
        """
        # NOTE: Do not override __hash__ function because BaseType instances isn't immutable
        if not getattr(self, '_hash', None):
            self._hash = self._to_hash_string()
        return self._hash

    def _to_hash_string(self) -> str:
        """
        Hash getter method to override

        :return:
        """
        raise NotImplementedError()


class UnknownType(BaseType):
    __slots__ = []

    def __str__(self):
        return "Unknown"

    def __iter__(self) -> Iterable['MetaData']:
        return iter(tuple())

    def replace(self, t: 'MetaData', **kwargs) -> 'UnknownType':
        return self

    def to_typing_code(self) -> Tuple[ImportPathList, str]:
        return ([('typing', 'Any')], 'Any')

    def to_hash_string(self) -> str:
        return "Unknown"


class NoneType(BaseType):
    __slots__ = []

    def __str__(self):
        return "NoneType"

    def __iter__(self) -> Iterable['MetaData']:
        return iter(tuple())

    def replace(self, t: 'MetaData', **kwargs) -> 'NoneType':
        return self

    def to_typing_code(self) -> Tuple[ImportPathList, str]:
        return ([], 'None')

    def to_hash_string(self) -> str:
        return "NoneType"


Unknown = UnknownType()
Null = NoneType()
MetaData = Union[type, dict, BaseType]


def get_hash_string(t: MetaData):
    if isinstance(t, dict):
        return str(hash(tuple((k, get_hash_string(v)) for k, v in t.items())))
    elif isclass(t):
        return str(t)
    elif isinstance(t, BaseType):
        return t.to_hash_string()
