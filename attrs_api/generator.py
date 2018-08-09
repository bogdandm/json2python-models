from enum import Enum
from typing import Optional, Callable, Iterable, Any, List, Union

import inflection

from .dynamic_typing import DList, DUnion, BaseType, DOptional, StringSerializable, STRING_CONVERTERS


class Hierarchy(Enum):
    Nested = "n"
    Plain = "p"


class OptionalFieldsPolicy(Enum):
    Optional = "o"
    FieldSets = "fs"


class SepStyle(Enum):
    Underscore = "_"
    Dash = "-"
    CamelCase = "CC"

    def __str__(self):
        return self.value


no_value = object()


# TODO: List of lists handler

class Generator:
    META_TYPE = Union[type, BaseType, dict, List[dict]]
    CONVERTER_TYPE = Optional[Callable[[str], Any]]
    DEFAULT_STRING_CONVERTERS = STRING_CONVERTERS

    def __init__(self,
                 sep_style: SepStyle = SepStyle.Underscore,
                 hierarchy: Hierarchy = Hierarchy.Nested,
                 fpolicy: OptionalFieldsPolicy = OptionalFieldsPolicy.Optional,
                 converters: Iterable[StringSerializable] = None):
        self.sep_style = sep_style
        self.hierarchy = hierarchy
        self.fpolicy = fpolicy
        self.converters = converters if converters is not None else self.DEFAULT_STRING_CONVERTERS

    def generate(self, *data_variants: dict):
        fields_sets = [self._convert(data) for data in data_variants]

    def _convert(self, data: dict):
        fields = dict()
        for key, value in data.items():
            fields[inflection.underscore(key)] = self._detect_type(value)
        return fields

    # def get_model(self, data: dict):

    # def get_attrib(self, value, complex_type=no_value):
    #     t = complex_type if complex_type is not no_value else self._detect_type(value)
    #     if isinstance(t, type):
    #         return attr.ib(type=t)
    #     else:
    #         return t

    def _detect_type(self, value, convert_dict=True) -> META_TYPE:
        # Simple types
        if isinstance(value, float):
            return float
        elif isinstance(value, bool):
            return bool
        elif isinstance(value, int):
            return int

        # List trying to yield nested type
        elif isinstance(value, list):
            if value:
                types = []
                for item in value:
                    t = self._detect_type(item, convert_dict)
                    types.append(t)
                if len(types) > 1:
                    return DList(DUnion(*types))
                else:
                    return DList(*types)
            else:
                return list

        # Dict should be processed as another model if convert_dict is enabled
        elif isinstance(value, dict):
            if convert_dict:
                return self._convert(value)
            else:
                return dict

        # null interpreted as Optional and will be processed later on merge stage
        elif value is None:
            return DOptional(Any)

        # string types trying to convert to other types
        else:  # string
            for converter in self.converters:
                try:
                    value = converter.to_internal_value(value)
                    if value is no_value:
                        continue
                except ValueError:
                    continue
                return converter
            return str
