from collections import OrderedDict
from enum import Enum
from typing import Optional, Callable, Iterable, Any, List, Union

import inflection

from .dynamic_typing import DList, DUnion, BaseType, DOptional, StringSerializable, STRING_CONVERTERS, NoneType


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

    def generate(self, *data_variants: dict) -> dict:
        fields_sets = [self._convert(data) for data in data_variants]
        fields = self._merge_field_sets(fields_sets)
        return fields

    def _convert(self, data: dict):
        fields = dict()
        for key, value in data.items():
            fields[inflection.underscore(key)] = self._detect_type(value)
        return fields

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
                    union = DUnion(*types)
                    if len(union.types) == 1:
                        return DList(*union.types)
                    return DList(union)
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

        # null interpreted as is and will be processed later on Union merge stage
        elif value is None:
            return NoneType

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

    def _merge_field_sets(self, field_sets: List[dict]) -> dict:
        fields = OrderedDict()

        first = True
        for model in field_sets:
            fields_diff = set(fields.keys())

            for name, field in model.items():
                if name not in fields:
                    fields[name] = field if first or isinstance(field, DOptional) else DOptional(field)
                else:
                    fields_diff.remove(name)
                    fields[name] = DUnion(
                        *(field.types if isinstance(field, DUnion) else [field]),
                        *(fields[name].types if isinstance(fields[name], DUnion) else [fields[name]])
                    )
                    if len(fields[name]) == 1:
                        fields[name] = fields[name].types[0]

            for name in fields_diff:
                if not isinstance(fields[name], DOptional):
                    fields[name] = DOptional(fields[name])

            first = False
        return fields
