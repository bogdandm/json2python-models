from collections import OrderedDict
from enum import Enum
from typing import Any, Callable, List, Optional, Union

from unidecode import unidecode

from .dynamic_typing import (ComplexType, DList, DOptional, DUnion, MetaData, ModelPtr, NoneType, SingleType,
                             StringSerializable, StringSerializableRegistry, Unknown, registry)


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


class MetadataGenerator:
    CONVERTER_TYPE = Optional[Callable[[str], Any]]

    # TODO: sep_style: SepStyle = SepStyle.Underscore
    # TODO: hierarchy: Hierarchy = Hierarchy.Nested
    # TODO: fpolicy: OptionalFieldsPolicy = OptionalFieldsPolicy.Optional

    def __init__(self, str_types_registry: StringSerializableRegistry = None):
        self.str_types_registry = str_types_registry if str_types_registry is not None else registry

    def generate(self, *data_variants: dict) -> dict:
        """
        Convert given list of data variants to metadata dict
        """
        fields_sets = [self._convert(data) for data in data_variants]
        fields = self.merge_field_sets(fields_sets)
        return self.optimize_type(fields)

    def _convert(self, data: dict):
        """
        Key and string value converting
        """
        fields = dict()
        for key, value in data.items():
            # TODO: Check if is 0xC0000005 crash has a place at linux systems
            # ! _detect_type function can crash at some complex data sets if value is unicode with some characters (maybe German)
            #   Crash does not produce any useful logs and can occur any time after bad string was processed
            #   It can be reproduced on real_apis tests (openlibrary API)
            fields[key] = self._detect_type(value if not isinstance(value, str) else unidecode(value))
        return fields

    def _detect_type(self, value, convert_dict=True) -> MetaData:
        """
        Converts json value to metadata
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

        # string types trying to convert to other string-serializable types
        else:
            for t in self.str_types_registry:
                try:
                    value = t.to_internal_value(value)
                except ValueError:
                    continue
                return t
            return str

    def merge_field_sets(self, field_sets: List[MetaData]) -> MetaData:
        """
        Merge fields sets into one set of pairs (key, metadata)
        """
        fields: dict = OrderedDict()

        first = True
        for model in field_sets:
            fields_diff = set(fields.keys())

            for name, field in model.items():
                if name not in fields:
                    # New field
                    field = field if first or isinstance(field, DOptional) else DOptional(field)
                else:
                    field_original = fields[name]
                    fields_diff.remove(name)
                    if isinstance(field_original, DOptional):
                        # Existing optional field
                        if field_original == field or field_original.type == field:
                            continue
                        field_original = field_original.type
                        field = DOptional(DUnion(
                            *(field.types if isinstance(field, DUnion) else [field]),
                            *(field_original.types if isinstance(field_original, DUnion) else [field_original])
                        ))
                        if len(field.type) == 1:
                            field.type = field.type.types[0]
                    else:
                        if field_original == field or (isinstance(field, DOptional) and field_original == field.type):
                            continue
                        field = DUnion(
                            *(field.types if isinstance(field, DUnion) else [field]),
                            *(field_original.types if isinstance(field_original, DUnion) else [field_original])
                        )
                        if len(field) == 1:
                            field = field.types[0]

                fields[name] = field

            for name in fields_diff:
                # Missing fields becomes optionals
                if not isinstance(fields[name], DOptional):
                    fields[name] = DOptional(fields[name])

            first = False
        return fields

    def optimize_type(self, meta: MetaData, process_model_ptr=False) -> MetaData:
        """
        Finds some redundant types and replace them with a simpler one

        :param process_model_ptr: Control whether process ModelPtr instances or not.
            Default is False to prevent recursion cycles.
        """
        if isinstance(meta, dict):
            fields = OrderedDict()

            for k, v in meta.items():
                fields[k] = self.optimize_type(v)
            return fields

        elif isinstance(meta, DUnion):
            return self._optimize_union(meta)

        elif isinstance(meta, SingleType) and (process_model_ptr or not isinstance(meta, ModelPtr)):
            # Optimize nested type
            return meta.replace(self.optimize_type(meta.type))

        elif isinstance(meta, ComplexType):
            # Optimize all nested types
            return meta.replace([self.optimize_type(nested) for nested in meta])
        return meta

    def _optimize_union(self, t: DUnion):
        # Replace DUnion of 1 element with this element
        if len(t) == 1:
            return t.types[0]

        # Split nested types into categories
        str_types: List[Union[type, StringSerializable]] = []
        types_to_merge: List[dict] = []
        list_types: List[DList] = []
        other_types: List[MetaData] = []
        for item in t.types:
            if isinstance(item, dict):
                types_to_merge.append(item)
            elif item in self.str_types_registry or item is str:
                str_types.append(item)
            elif isinstance(item, DList):
                list_types.append(item)
            else:
                other_types.append(item)

        if int in other_types and float in other_types:
            other_types.remove(int)

        if types_to_merge:
            other_types.append(self.merge_field_sets(types_to_merge))

        if list_types:
            other_types.append(DList(DUnion(*(
                t.type for t in list_types
            ))))

        if str in str_types:
            other_types.append(str)
        elif str_types:
            str_types = self.str_types_registry.resolve(*str_types)
            # Replace str pseudo-types with <class 'str'> when they can not be resolved into single type
            other_types.append(str if len(str_types) > 1 else next(iter(str_types)))

        types = [self.optimize_type(t) for t in other_types]

        if Unknown in types:
            types.remove(Unknown)

        if len(types) > 1:
            if NoneType in types:
                types.remove(NoneType)
                if len(types) > 1:
                    return DOptional(DUnion(*types))
                else:
                    return DOptional(types[0])
            return DUnion(*types)

        else:
            return types[0]
