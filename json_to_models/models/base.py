import keyword
import re
from typing import Iterable, List, Tuple, Type

import inflection
from jinja2 import Template
from unidecode import unidecode

from . import INDENT, ModelsStructureType, OBJECTS_DELIMITER
from .string_converters import get_string_field_paths
from .structure import sort_fields
from .utils import indent
from ..dynamic_typing import (AbsoluteModelRef, ImportPathList, MetaData,
                              ModelMeta, compile_imports, metadata_to_typing)
from ..utils import cached_classmethod

METADATA_FIELD_NAME = "J2M_ORIGINAL_FIELD"
KWAGRS_TEMPLATE = "{% for key, value in kwargs.items() %}" \
                  "{{ key }}={{ value }}" \
                  "{% if not loop.last %}, {% endif %}" \
                  "{% endfor %}"

keywords_set = set(keyword.kwlist)
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
    class {{ name }}:
    
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

    def __init__(self, model: ModelMeta, post_init_converters=False):
        self.model = model
        self.post_init_converters = post_init_converters

    @cached_classmethod
    def convert_field_name(cls, name):
        if name in keywords_set:
            name += "_"
        name = unidecode(name)
        name = re.sub(r"\W", "", name)
        if not ('a' <= name[0].lower() <= 'z'):
            if '0' <= name[0] <= '9':
                name = ones[int(name[0])] + "_" + name[1:]
        return inflection.underscore(name)

    def generate(self, nested_classes: List[str] = None, extra: str = "") -> Tuple[ImportPathList, str]:
        """
        :param nested_classes: list of strings that contains classes code
        :return: list of import data, class code
        """
        imports, fields = self.fields
        decorator_imports, decorators = self.decorators
        data = {
            "decorators": decorators,
            "name": self.model.name,
            "fields": fields,
            "extra": extra
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
        imports, typing = metadata_to_typing(meta)

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
        required, optional = sort_fields(self.model)
        imports: ImportPathList = []
        strings: List[str] = []
        for is_optional, fields in enumerate((required, optional)):
            for field in fields:
                field_imports, data = self.field_data(field, self.model.type[field], bool(is_optional))
                imports.extend(field_imports)
                strings.append(self.FIELD.render(**data))
        return imports, strings

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
    Walk thought models structure and covert them into code

    :param structure: Result of compose_models or similar function
    :param class_generator: GenericModelCodeGenerator subclass
    :param class_generator_kwargs: kwags for GenericModelCodeGenerator init
    :param lvl: Recursion depth
    :return: imports, list of first lvl classes
    """
    imports = []
    classes = []
    for data in structure:
        nested_imports, nested_classes = _generate_code(
            data["nested"],
            class_generator,
            class_generator_kwargs,
            lvl=lvl + 1
        )
        imports.extend(nested_imports)
        gen = class_generator(data["model"], **class_generator_kwargs)
        cls_imports, cls_string = gen.generate(nested_classes)
        imports.extend(cls_imports)
        classes.append(cls_string)
    return imports, classes


def generate_code(structure: ModelsStructureType, class_generator: Type[GenericModelCodeGenerator],
                  class_generator_kwargs: dict = None, objects_delimiter: str = OBJECTS_DELIMITER) -> str:
    """
    Generate ready-to-use code

    :param structure: Result of compose_models or similar function
    :param class_generator: GenericModelCodeGenerator subclass
    :param class_generator_kwargs: kwags for GenericModelCodeGenerator init
    :param objects_delimiter: Delimiter between root level classes
    :return: Generated code
    """
    root, mapping = structure
    with AbsoluteModelRef.inject(mapping):
        imports, classes = _generate_code(root, class_generator, class_generator_kwargs or {})
    if imports:
        imports_str = compile_imports(imports) + objects_delimiter
    else:
        imports_str = ""
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
