import re
from typing import Any, Callable, List, Optional, Pattern, Union

from unidecode import unidecode

from .dynamic_typing import (ComplexType, DDict, DList, DOptional, DUnion, MetaData, ModelPtr, Null, SingleType,
                             StringSerializable, StringSerializableRegistry, Unknown, registry)

_static_types = {float, bool, int}

class MetadataGenerator:
    CONVERTER_TYPE = Optional[Callable[[str], Any]]

    def __init__(
            self,
            str_types_registry: StringSerializableRegistry = None,
            dict_keys_regex: List[Union[Pattern, str]] = None,
            dict_keys_fields: List[str] = None
    ):
        """

        :param str_types_registry: StringSerializableRegistry instance. Default registry will be used if None passed .
        :param dict_keys_regex: List of RegExpressions (compiled or not).
            If all keys of some dict are match one of them then this dict will be marked as dict field
            but not nested model.
        :param dict_keys_fields: List of model fields names that will be marked as dict field
        """
        self.str_types_registry = str_types_registry if str_types_registry is not None else registry
        self.dict_keys_regex = [re.compile(r) for r in dict_keys_regex] if dict_keys_regex else []
        self.dict_keys_fields = set(dict_keys_fields or ())

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
            convert_dict = key not in self.dict_keys_fields
            fields[key] = self._detect_type(value if not isinstance(value, str) else unidecode(value), convert_dict)
        return fields

    def _detect_type(self, value, convert_dict=True) -> MetaData:
        """
        Converts json value to metadata
        """
        # Simple types
        t = type(value)
        if t in _static_types:
            return t

        # List trying to yield nested type
        elif t is list:
            if value:
                types = [self._detect_type(item) for item in value]
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
            if not value:
                return DDict(Unknown)
            for reg in self.dict_keys_regex:
                if all(map(reg.match, value.keys())):
                    convert_dict = False
                    break

            if convert_dict:
                return self._convert(value)
            else:
                types = [self._detect_type(item) for item in value.values()]
                if len(types) > 1:
                    union = DUnion(*types)
                    if len(union.types) == 1:
                        return DDict(*union.types)
                    return DDict(union)
                else:
                    return DDict(*types)

        # null interpreted as is and will be processed later on Union merge stage
        elif value is None:
            return Null

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
        fields: dict = {}

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
            fields = {}

            for k, v in meta.items():
                fields[k] = self.optimize_type(v)
            return fields

        elif isinstance(meta, DUnion):
            return self._optimize_union(meta)

        elif isinstance(meta, DOptional):
            t = self.optimize_type(meta.type)
            if isinstance(t, DOptional):
                t = t.type
            return meta.replace(t)

        elif isinstance(meta, SingleType) and (process_model_ptr or not isinstance(meta, ModelPtr)):
            # Optimize nested type
            return meta.replace(self.optimize_type(meta.type))

        elif isinstance(meta, ComplexType):
            # Optimize all nested types
            return meta.replace([self.optimize_type(nested) for nested in meta])
        return meta

    def _optimize_union(self, t: DUnion):
        # Replace DUnion of 1 element with this element
        # if len(t) == 1:
        #     return t.types[0]

        # Split nested types into categories
        str_types: List[Union[type, StringSerializable]] = []
        types_to_merge: List[dict] = []
        list_types: List[DList] = []
        dict_types: List[DList] = []
        other_types: List[MetaData] = []
        for item in t.types:
            if isinstance(item, DOptional):
                item = item.type
                other_types.append(Null)
            if isinstance(item, dict):
                types_to_merge.append(item)
            elif item in self.str_types_registry or item is str:
                str_types.append(item)
            elif isinstance(item, DList):
                list_types.append(item)
            elif isinstance(item, DDict):
                dict_types.append(item)
            else:
                other_types.append(item)

        if int in other_types and float in other_types:
            other_types.remove(int)

        if types_to_merge:
            other_types.append(self.merge_field_sets(types_to_merge))

        for cls, iterable_types in ((DList, list_types), (DDict, dict_types)):
            if iterable_types:
                other_types.append(cls(DUnion(*(
                    t.type for t in iterable_types
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

        optional = False
        if Null in types:
            optional = True
            while Null in types:
                types.remove(Null)

        if len(types) > 1:
            meta_type = DUnion(*types)
            if len(meta_type.types) == 1:
                meta_type = meta_type.types[0]
        else:
            meta_type = types[0]

        if optional:
            return DOptional(meta_type)
        else:
            return meta_type
