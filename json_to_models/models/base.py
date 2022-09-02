import copy
import keyword
import re
from typing import Dict, Iterable, List, Tuple, Type, Union

import inflection
from jinja2 import Template
from unidecode import unidecode

from . import INDENT, ModelsStructureType, OBJECTS_DELIMITER
from .string_converters import get_string_field_paths
from .structure import sort_fields
from .utils import indent
from ..dynamic_typing import (AbsoluteModelRef, BaseType, ImportPathList, MetaData,
                              ModelMeta, StringLiteral, compile_imports, metadata_to_typing)
from ..utils import cached_method

METADATA_FIELD_NAME = "J2M_ORIGINAL_FIELD"
KWAGRS_TEMPLATE = "{% for key, value in kwargs.items() %}" \
                  "{{ key }}={{ value }}" \
                  "{% if not loop.last %}, {% endif %}" \
                  "{% endfor %}"

keywords_set = set(keyword.kwlist)
builtins_set = set(__builtins__.keys())
other_common_names_set = {'datetime', 'time', 'date', 'defaultdict', 'schema'}
blacklist_words = frozenset(keywords_set | builtins_set | other_common_names_set)
ones = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']


def template(pattern: str, indent: str = INDENT) -> Template:
    """
    Remove indent from triple-quotes string and return jinja2.Template instance
    """
    if "\n" in pattern:
        n = len(indent)
        lines = pattern.split("\n")
        for i in (0, -1):
            if not lines[i].strip():
                del lines[i]

        pattern = "\n".join(line[n:] if line[:n] == indent else line
                            for line in lines)
    return Template(pattern)


class GenericModelCodeGenerator:
    """
    Core of model code generator. Extend it to customize fields of model or add some decorators.
    Note that this class has nothing to do with models structure. It only can add nested models as strings.
    """
    BODY = template("""
    {%- for decorator in decorators -%}
    @{{ decorator }}
    {% endfor -%}
    class {{ name }}{% if bases %}({{ bases }}){% endif %}:

    {%- for code in nested %}
    {{ code }}
    {% endfor -%}

    {%- if fields -%}
    {%- for field in fields %}
        {{ field }}
    {%- endfor %}
    {%- else %}
        pass
    {%- endif -%}
    {%- if extra %}
    {{ extra }}
    {%- endif -%}
    """)

    STR_CONVERT_DECORATOR = template("convert_strings({{ str_fields }}{%% if kwargs %%}, %s{%% endif %%})"
                                     % KWAGRS_TEMPLATE)
    FIELD: Template = template("{{name}}: {{type}}{% if body %} = {{ body }}{% endif %}")
    DEFAULT_MAX_LITERALS = 10
    default_types_style = {
        StringLiteral: {
            StringLiteral.TypeStyle.use_literals: True
        }
    }

    def __init__(
            self,
            model: ModelMeta,
            max_literals=DEFAULT_MAX_LITERALS,
            post_init_converters=False,
            convert_unicode=True,
            types_style: Dict[Union['BaseType', Type['BaseType']], dict] = None
    ):
        self.model = model
        self.post_init_converters = post_init_converters
        self.convert_unicode = convert_unicode

        resolved_types_style = copy.deepcopy(self.default_types_style)
        types_style = types_style or {}
        for t, style in types_style.items():
            resolved_types_style.setdefault(t, {})
            resolved_types_style[t].update(style)
        resolved_types_style[StringLiteral][StringLiteral.TypeStyle.max_literals] = int(max_literals)
        self.types_style = resolved_types_style

        self.model.set_raw_name(self.convert_class_name(self.model.name), generated=self.model.is_name_generated)

    @cached_method
    def convert_class_name(self, name):
        return prepare_label(name, convert_unicode=self.convert_unicode, to_snake_case=False)

    @cached_method
    def convert_field_name(self, name):
        return prepare_label(name, convert_unicode=self.convert_unicode, to_snake_case=True)

    def generate(self, nested_classes: List[str] = None, bases: str = None, extra: str = "") \
            -> Tuple[ImportPathList, str]:
        """
        :param nested_classes: list of strings that contains classes code
        :return: list of import data, class code
        """
        imports, fields = self.fields
        decorator_imports, decorators = self.decorators
        data = {
            "decorators": decorators,
            "name": self.model.name,
            "bases": bases or [],
            "fields": fields,
            "extra": extra,
        }
        if nested_classes:
            data["nested"] = [indent(s) for s in nested_classes]
        return [*imports, *decorator_imports], self.BODY.render(**data)

    @property
    def decorators(self) -> Tuple[ImportPathList, List[str]]:
        """
        :return: List of imports and List of decorators code (without @)
        """
        imports, decorators = [], []
        if self.post_init_converters:
            str_fields = self.string_field_paths
            decorator_imports, decorator_kwargs = self.convert_strings_kwargs
            if str_fields and decorator_kwargs:
                imports.extend([
                    *decorator_imports,
                    ('json_to_models.models.string_converters', ['convert_strings']),
                ])
                decorators.append(self.STR_CONVERT_DECORATOR.render(str_fields=str_fields, kwargs=decorator_kwargs))
        return imports, decorators

    def field_data(self, name: str, meta: MetaData, optional: bool) -> Tuple[ImportPathList, dict]:
        """
        Form field data for template

        :param name: Original field name
        :param meta: Field metadata
        :param optional: Is field optional
        :return: imports, field data
        """
        imports, typing = metadata_to_typing(meta, types_style=self.types_style)

        data = {
            "name": self.convert_field_name(name),
            "type": typing
        }
        return imports, data

    @property
    def fields(self) -> Tuple[ImportPathList, List[str]]:
        """
        Generate fields strings

        :return: imports, list of fields as string
        """
        required, optional = sort_fields(self.model, unicode_fix=not self.convert_unicode)
        imports: ImportPathList = []
        strings: List[str] = []
        for is_optional, fields in enumerate((required, optional)):
            fields = self._filter_fields(fields)
            for field in fields:
                field_imports, data = self.field_data(field, self.model.type[field], bool(is_optional))
                imports.extend(field_imports)
                strings.append(self.FIELD.render(**data))
        return imports, strings

    def _filter_fields(self, fields):
        return fields

    @property
    def string_field_paths(self) -> List[str]:
        """
        Get paths for convert_strings function
        """
        return [self.convert_field_name(name) + ('#' + '.'.join(path) if path else '')
                for name, path in get_string_field_paths(self.model)]

    @property
    def convert_strings_kwargs(self) -> Tuple[ImportPathList, dict]:
        """
        Override it to enable generation of string types converters

        :return: Imports and Dict with kw-arguments for `json_to_models.models.string_converters.convert_strings` decorator.
        """
        return [], {}


def _generate_code(
        structure: List[dict],
        class_generator: Type[GenericModelCodeGenerator],
        class_generator_kwargs: dict,
        lvl=0
) -> Tuple[ImportPathList, List[str]]:
    """
    Walk through the model structures and convert them into code

    :param structure: Result of compose_models or similar function
    :param class_generator: GenericModelCodeGenerator subclass
    :param class_generator_kwargs: kwags for GenericModelCodeGenerator init
    :param lvl: Recursion depth
    :return: imports, list of first lvl classes
    """
    imports = []
    classes = []
    generators = []
    for data in structure:
        nested_imports, nested_classes = _generate_code(
            data["nested"],
            class_generator,
            class_generator_kwargs,
            lvl=lvl + 1
        )
        imports.extend(nested_imports)
        generators.append((
            class_generator(data["model"], **class_generator_kwargs),
            nested_classes
        ))
    for gen, nested_classes in generators:
        cls_imports, cls_string = gen.generate(nested_classes)
        imports.extend(cls_imports)
        classes.append(cls_string)
    return imports, classes


def generate_code(structure: ModelsStructureType, class_generator: Type[GenericModelCodeGenerator],
                  class_generator_kwargs: dict = None,
                  objects_delimiter: str = OBJECTS_DELIMITER,
                  preamble: str = None) -> str:
    """
    Generate ready-to-use code

    :param structure: Result of compose_models or similar function
    :param class_generator: GenericModelCodeGenerator subclass
    :param class_generator_kwargs: kwags for GenericModelCodeGenerator init
    :param objects_delimiter: Delimiter between root level classes
    :param preamble: code to insert after the imports and before the classes
    :return: Generated code
    """
    root, mapping = structure
    with AbsoluteModelRef.inject(mapping):
        imports, classes = _generate_code(root, class_generator, class_generator_kwargs or {})
        imports_str = ""
    if imports:
        imports_str = compile_imports(imports) + objects_delimiter
    if preamble:
        imports_str += preamble + objects_delimiter

    return imports_str + objects_delimiter.join(classes) + "\n"


def sort_kwargs(kwargs: dict, ordering: Iterable[Iterable[str]]) -> dict:
    sorted_dict_1 = {}
    sorted_dict_2 = {}
    current = sorted_dict_1
    for group in ordering:
        if isinstance(group, str):
            if group != "*":
                raise ValueError(f"Unknown kwarg group: {group}")
            current = sorted_dict_2
        else:
            for item in group:
                if item in kwargs:
                    value = kwargs.pop(item)
                    current[item] = value
    sorted_dict = {**sorted_dict_1, **kwargs, **sorted_dict_2}
    return sorted_dict


def prepare_label(s: str, convert_unicode: bool, to_snake_case: bool) -> str:
    if convert_unicode:
        s = unidecode(s)
    s = re.sub(r"\W", "", s)
    if not ('a' <= s[0].lower() <= 'z'):
        if '0' <= s[0] <= '9':
            s = ones[int(s[0])] + "_" + s[1:]
    if to_snake_case:
        s = inflection.underscore(s)
    if s in blacklist_words:
        s += "_"
    return s
