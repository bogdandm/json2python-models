from inspect import isclass
from typing import Any, Callable, List, Tuple

from .base import GenericModelCodeGenerator, KWAGRS_TEMPLATE, METADATA_FIELD_NAME, sort_kwargs, template
from ..dynamic_typing import (BaseType, DDict, DList, DOptional, DUnion, ImportPathList, MetaData, ModelMeta, ModelPtr,
                              StringSerializable)

DEFAULT_ORDER = (
    ("default", "default_factory"),
    "*",
    ("metadata",)
)


def _process_string_field_value(path: List[str], value: Any, current_type: Any, optional=False) -> Any:
    token, *path = path
    if token == 'S':
        try:
            value = current_type.to_internal_value(value)
        except ValueError as e:
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


def dataclass_post_init_converters(str_fields: List[str]):
    """
    Method factory. Return post_init method to convert string into StringSerializable types
    To override generated __post_init__ you can call it directly:

    >>> def __post_init__(self):
    ...     dataclass_post_init_converters(['a', 'b'])(self)

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

    return __post_init__


def convert_strings(str_field_paths: List[str]) -> Callable[[type], type]:
    """
    Decorator factory. Set up `__post_init__` method to convert strings fields values into StringSerializable types

    If field contains complex data type path should be consist of field name and dotted list of tokens:

    * `S` - string component
    * `O` - Optional
    * `L` - List
    * `D` - Dict

    So if field `'bar'` has type `Optional[List[List[IntString]]]` field path would be `'bar#O.L.L.S'`

    ! If type is too complex i.e. Union[List[IntString], List[List[IntString]]]
    you can't specify field path and such field would be ignored

    :param str_field_paths: Paths of StringSerializable fields (field name or field name + typing path)
    :return: Class decorator
    """

    def decorator(cls: type) -> type:
        if hasattr(cls, '__post_init__'):
            old_fn = cls.__post_init__

            def __post_init__(self, *args, **kwargs):
                dataclass_post_init_converters(str_field_paths)(self)
                old_fn(self, *args, **kwargs)

            setattr(cls, '__post_init__', __post_init__)
        else:
            setattr(cls, '__post_init__', dataclass_post_init_converters(str_field_paths))

        return cls

    return decorator


class DataclassModelCodeGenerator(GenericModelCodeGenerator):
    DC_DECORATOR = template(f"dataclass{{% if kwargs %}}({KWAGRS_TEMPLATE}){{% endif %}}")
    DC_CONVERT_DECORATOR = template("convert_strings({{ str_fields }})")
    DC_FIELD = template(f"field({KWAGRS_TEMPLATE})")

    def __init__(self, model: ModelMeta, meta=False, post_init_converters=False, dataclass_kwargs: dict = None,
                 **kwargs):
        """
        :param model: ModelMeta instance
        :param meta: Enable generation of metadata as attrib argument
        :param post_init_converters: Enable generation of type converters in __post_init__ methods
        :param dataclass_kwargs: kwargs for @dataclass() decorators
        :param kwargs:
        """
        super().__init__(model, **kwargs)
        self.post_init_converters = post_init_converters
        self.no_meta = not meta
        self.dataclass_kwargs = dataclass_kwargs or {}

    def get_string_field_paths(self) -> List[str]:
        # `S` - string component
        # `O` - Optional
        # `L` - List
        # `D` - Dict
        str_fields = []
        for name, t in self.model.type.items():
            name = self.convert_field_name(name)

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
                    else:
                        raise TypeError(f"Unsupported meta-type for converter path {cls}")

                    for nested_type in tmp_type:
                        tokens.append((nested_type, path + [token]))
            paths: List[str] = ["".join(p[1:]) for p in paths]
            if len(paths) != 1:
                continue

            path = paths.pop()
            if path == 'S':
                str_fields.append(name)
            else:
                str_fields.append(f'{name}#{".".join(path)}')

        return str_fields

    @property
    def decorators(self) -> Tuple[ImportPathList, List[str]]:
        imports = [('dataclasses', ['dataclass', 'field'])]
        decorators = [self.DC_DECORATOR.render(kwargs=self.dataclass_kwargs)]

        if self.post_init_converters:
            str_fields = self.get_string_field_paths()
            if str_fields:
                imports.append(('json_to_models.models.dataclasses', ['convert_strings']))
                decorators.append(self.DC_CONVERT_DECORATOR.render(str_fields=str_fields))

        return imports, decorators

    def field_data(self, name: str, meta: MetaData, optional: bool) -> Tuple[ImportPathList, dict]:
        """
        Form field data for template

        :param name: Original field name
        :param meta: Field metadata
        :param optional: Is field optional
        :return: imports, field data
        """
        imports, data = super().field_data(name, meta, optional)
        body_kwargs = {}
        if optional:
            meta: DOptional
            if isinstance(meta.type, DList):
                body_kwargs["default_factory"] = "list"
            elif isinstance(meta.type, DDict):
                body_kwargs["default_factory"] = "dict"
            else:
                body_kwargs["default"] = "None"
                if isclass(meta.type) and issubclass(meta.type, StringSerializable):
                    pass
        elif isclass(meta) and issubclass(meta, StringSerializable):
            pass

        if not self.no_meta and name != data["name"]:
            body_kwargs["metadata"] = {METADATA_FIELD_NAME: name}
        if len(body_kwargs) == 1 and next(iter(body_kwargs.keys())) == "default":
            data["body"] = body_kwargs["default"]
        elif body_kwargs:
            data["body"] = self.DC_FIELD.render(kwargs=sort_kwargs(body_kwargs, DEFAULT_ORDER))
        return imports, data
