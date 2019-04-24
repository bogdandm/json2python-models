from functools import wraps
from inspect import isclass
from typing import Any, Callable, List, Optional, Tuple

from . import ClassType
from ..dynamic_typing import (BaseType, DDict, DList, DOptional, DUnion, MetaData, ModelMeta, ModelPtr,
                              StringSerializable)
from ..dynamic_typing.base import NoneType


def convert_strings(str_field_paths: List[str], class_type: Optional[ClassType] = None,
                    method: Optional[str] = None) -> Callable[[type], type]:
    """
    Decorator factory. Set up post-init method to convert strings fields values into StringSerializable types

    If field contains complex data type path should be consist of field name and dotted list of tokens:

    * `S` - string component
    * `O` - Optional
    * `L` - List
    * `D` - Dict

    So if field `'bar'` has type `Optional[List[List[IntString]]]` field path would be `'bar#O.L.L.S'`

    ! If type is too complex i.e. Union[List[IntString], List[List[IntString]]]
    you can't specify field path and such field would be ignored

    To specify name of post-init method you should provide it by class_type argument or directly by method argument:

    >>> convert_strings([...], class_type=ClassType.Attrs)

    is equivalent of

    >>> convert_strings([...], method="__attrs_post_init__")

    :param str_field_paths: Paths of StringSerializable fields (field name or field name + typing path)
    :param class_type: attrs | dataclass - type of decorated class
    :param method: post-init method name
    :return: Class decorator
    """
    method = {
        ClassType.Attrs: '__attrs_post_init__',
        ClassType.Dataclass: '__post_init__',
        None: method
    }.get(class_type)

    def decorator(cls: type) -> type:
        if hasattr(cls, method):
            old_fn = getattr(cls, method)

            @wraps(old_fn)
            def __post_init__(self, *args, **kwargs):
                post_init_converters(str_field_paths)(self)
                old_fn(self, *args, **kwargs)

            setattr(cls, method, __post_init__)
        else:
            fn = post_init_converters(str_field_paths)
            fn.__name__ = method
            setattr(cls, method, fn)

        return cls

    return decorator


def post_init_converters(str_fields: List[str], wrap_fn=None):
    """
    Method factory. Return post_init method to convert string into StringSerializable types
    To override generated __post_init__ you can call it directly:

    >>> def __post_init__(self):
    ...     post_init_converters(['a', 'b'])(self)

    :param str_fields: names of StringSerializable fields
    :return: __post_init__ method
    """

    def __post_init__(self):
        # `S` - string component
        # `O` - Optional
        # `L` - List
        # `D` - Dict
        for name in str_fields:
            if '#' in name:
                name, path_str = name.split('#')
                path: List[str] = path_str.split('.')
            else:
                path = ['S']

            new_value = _process_string_field_value(
                path=path,
                value=getattr(self, name),
                current_type=self.__annotations__[name]
            )
            setattr(self, name, new_value)

    if wrap_fn:
        __post_init__ = wraps(wrap_fn)(__post_init__)

    return __post_init__


def _process_string_field_value(path: List[str], value: Any, current_type: Any, optional=False) -> Any:
    token, *path = path
    if token == 'S':
        try:
            value = current_type.to_internal_value(value)
        except (ValueError, TypeError) as e:
            if not optional:
                raise e
        return value
    elif token == 'O':
        return _process_string_field_value(
            path=path,
            value=value,
            current_type=current_type.__args__[0],
            optional=True
        )
    elif token == 'L':
        t = current_type.__args__[0]
        return [
            _process_string_field_value(path, item, current_type=t, optional=optional)
            for item in value
        ]
    elif token == 'D':
        t = current_type.__args__[1]
        return {
            key: _process_string_field_value(path, item, current_type=t, optional=optional)
            for key, item in value.items()
        }
    else:
        raise ValueError(f"Unknown token {token}")


def get_string_field_paths(model: ModelMeta) -> List[Tuple[str, List[str]]]:
    """
    Return paths for convert_strings function of given model

    :return: Paths with raw names
    """
    # `S` - string component
    # `O` - Optional
    # `L` - List
    # `D` - Dict
    str_fields: List[Tuple[str, List[str]]] = []
    for name, t in model.type.items():

        # Walk through nested types
        paths: List[List[str]] = []
        tokens: List[Tuple[MetaData, List[str]]] = [(t, ['#'])]
        while tokens:
            tmp_type, path = tokens.pop()
            if isclass(tmp_type):
                if issubclass(tmp_type, StringSerializable):
                    paths.append(path + ['S'])
            elif isinstance(tmp_type, BaseType):
                cls = type(tmp_type)
                if cls is DOptional:
                    token = 'O'
                elif cls is DList:
                    token = 'L'
                elif cls is DDict:
                    token = 'D'
                elif cls in (DUnion, ModelPtr):
                    # We could not resolve Union
                    paths = []
                    break
                elif cls is NoneType:
                    continue
                else:
                    raise TypeError(f"Unsupported meta-type for converter path {cls}")

                for nested_type in tmp_type:
                    tokens.append((nested_type, path + [token]))
        paths: List[str] = ["".join(p[1:]) for p in paths]
        if len(paths) != 1:
            continue

        path = paths.pop()
        if path == 'S':
            str_fields.append((name, []))
        else:
            str_fields.append((name, path))

    return str_fields
