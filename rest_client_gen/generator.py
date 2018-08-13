from collections import OrderedDict
from enum import Enum
from typing import Optional, Callable, Any, List, Union

import inflection

from .dynamic_typing import (
    BaseType, SingleType,
    DList, DUnion, DOptional, NoneType,
    StringSerializableRegistry, registry,
    ComplexType, Unknown
)


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


class Generator:
    META_TYPE = Union[type, BaseType, dict]
    CONVERTER_TYPE = Optional[Callable[[str], Any]]

    def __init__(self,
                 sep_style: SepStyle = SepStyle.Underscore,
                 hierarchy: Hierarchy = Hierarchy.Nested,
                 fpolicy: OptionalFieldsPolicy = OptionalFieldsPolicy.Optional,
                 str_types_registry: StringSerializableRegistry = None):
        self.sep_style = sep_style
        self.hierarchy = hierarchy
        self.fpolicy = fpolicy
        self.str_types_registry = str_types_registry if str_types_registry is not None else registry

    def generate(self, *data_variants: dict) -> dict:
        fields_sets = [self._convert(data) for data in data_variants]
        fields = self._merge_field_sets(fields_sets)
        return self._optimize_type(fields)

    def _convert(self, data: dict):
        fields = dict()
        for key, value in data.items():
            fields[inflection.underscore(key)] = self._detect_type(value)
        return fields

    def _detect_type(self, value, convert_dict=True) -> META_TYPE:
        """
        Converts json value to meta-type
        """
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
                return DList(Unknown)

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
            for t in self.str_types_registry:
                try:
                    value = t.to_internal_value(value)
                except ValueError:
                    continue
                return t
            return str

    def _merge_field_sets(self, field_sets: List[dict]) -> OrderedDict:
        """
        Merges fields sets into one set of pairs key - meta-type
        """
        fields = OrderedDict()

        first = True
        for model in field_sets:
            fields_diff = set(fields.keys())

            for name, field in model.items():
                if name not in fields:
                    field = field if first or isinstance(field, DOptional) else DOptional(field)
                else:
                    fields_diff.remove(name)
                    field = DUnion(
                        *(field.types if isinstance(field, DUnion) else [field]),
                        *(fields[name].types if isinstance(fields[name], DUnion) else [fields[name]])
                    )
                fields[name] = field

            for name in fields_diff:
                if not isinstance(fields[name], DOptional):
                    fields[name] = DOptional(fields[name])

            first = False
        return fields

    def _optimize_type(self, t: META_TYPE) -> META_TYPE:
        """
        Finds some redundant types and replace them with simple one
        """
        if isinstance(t, dict):
            fields = OrderedDict()

            for k, v in t.items():
                fields[k] = self._optimize_type(v)
            return fields

        elif isinstance(t, DUnion):
            # Replace DUnion of 1 element with this element
            if len(t) == 1:
                return t.types[0]

            # Optimize nested types and merge str pseudo-types
            str_types = []
            types_to_merge = []
            other_types = []
            for item in t.types:
                if isinstance(item, dict):
                    types_to_merge.append(item)
                elif item in self.str_types_registry:
                    str_types.append(item)
                else:
                    other_types.append(self._optimize_type(item))

            if int in other_types and float in other_types:
                other_types.remove(int)

            if types_to_merge:
                types_to_merge = [self._optimize_type(self._merge_field_sets(types_to_merge))]

            str_types = self.str_types_registry.resolve(*str_types)
            # Replace str pseudo-types with <class 'str'> when they can not be resolved into single type
            if len(str_types) > 1:
                str_types = [str]

            types = [*other_types, *str_types, *types_to_merge]
            if len(types) > 1:
                return DUnion(*types)
            else:
                return types[0]

        elif isinstance(t, SingleType):
            # Optimize nested types
            return t.__class__(self._optimize_type(t.type))

        elif isinstance(t, ComplexType):
            # Optimize all nested types
            return t.__class__(*map(self._optimize_type, t.types))
        return t
