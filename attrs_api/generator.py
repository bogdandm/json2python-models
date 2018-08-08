from enum import Enum
from typing import Optional, Callable, Iterable, Tuple, Any, List, Union

import attr
import inflection

from .dynamic_typing import DList, DUnion, BaseType, DOptional


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
    converters: Iterable[Tuple[META_TYPE, CONVERTER_TYPE]] = (
        (int, int),
        (float, float),
        (bool, lambda v: {"true": True, "false": False}.get(v.lower(), no_value))
    )

    def __init__(self,
                 sep_style: SepStyle = SepStyle.Underscore,
                 hierarchy: Hierarchy = Hierarchy.Nested,
                 fpolicy: OptionalFieldsPolicy = OptionalFieldsPolicy.Optional,
                 converters: Iterable[Tuple[META_TYPE, CONVERTER_TYPE]] = None):
        self.sep_style = sep_style
        self.hierarchy = hierarchy
        self.fpolicy = fpolicy
        self.converters = converters if converters is not None else self.converters

    def generate(self, *data_variants: dict):
        fields_sets = [self._convert(data) for data in data_variants]

    def _convert(self, data: dict):
        fields = dict()
        for key, value in data.items():
            key = inflection.underscore(key)
            if isinstance(value, dict):
                a = self._convert(value)
            else:
                a = self.get_attrib(value)
            fields[key] = a
        return fields

    # def get_model(self, data: dict):

    def get_attrib(self, value, complex_type=no_value):
        t, converter = complex_type if complex_type is not no_value else self._detect_type(value)
        if isinstance(t, type):
            return attr.ib(type=t, converter=converter)
        else:
            return t

    def _detect_type(self, value, convert_dict=True) -> Tuple[META_TYPE, CONVERTER_TYPE]:
        # Simple types
        if isinstance(value, float):
            return float, None
        elif isinstance(value, bool):
            return bool, None
        elif isinstance(value, int):
            return int, None

        # List trying to yield nested type
        elif isinstance(value, list):
            if value:
                types = []
                for item in value:
                    t, _ = self._detect_type(item, convert_dict)
                    types.append(t)
                if len(types) > 1:
                    return DList(DUnion(*types)), None
                else:
                    return DList(*types), None
            else:
                return list, None

        # Dict should be processed as another model in _convert else they interpreted as is
        elif isinstance(value, dict):
            if convert_dict:
                return self._convert(value), None
            else:
                return dict, None

        # null interpreted as Optional and will be processed later on merge stage
        elif value is None:
            return DOptional(Any), None

        # string types trying to convert to other types
        else:  # string
            for t, converter in self.converters:
                try:
                    value = converter(value)
                    if value is no_value:
                        continue
                except ValueError:
                    continue
                return t, converter
            return str, None
