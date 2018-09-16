from typing import Iterable, List, Tuple, Union

ImportPathList = List[Tuple[str, Union[Iterable[str], str]]]


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

    def to_typing_code(self) -> Tuple[ImportPathList, str]:
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

    def to_typing_code(self) -> Tuple[ImportPathList, str]:
        return ([('typing', 'Any')], 'Any')


Unknown = UnknownType()
NoneType = type(None)
MetaData = Union[type, dict, BaseType]
