import re
from typing import List, Tuple, Type

import chevron

from rest_client_gen.dynamic_typing import compile_imports
from . import sort_fields
from ..dynamic_typing import ImportPathList, MetaData, ModelMeta, metadata_to_typing

INDENT = "    "
RE_REMOVE = re.compile("\$\s+\$")


def fix_patterns(indent: str = INDENT):
    """
    Fix all multiline strings constants:
    * Remove indent
    * Remove empty spaces between $ $
    * Replace indent with INDENT
    """

    def decorator(cls):
        n = len(indent)
        for attr in dir(cls):
            if attr.isupper():
                value = getattr(cls, attr)
                value = RE_REMOVE.sub("", value)
                if isinstance(value, str) and "\n" in value:
                    lines = value.split("\n")
                    for i in (0, -1):
                        if not lines[i].strip():
                            del lines[i]

                    for i in range(len(lines)):
                        line = lines[i]
                        line = line[n:] if lines[i][:n] == indent else lines[i]
                        line.replace("    ", INDENT)
                        lines[i] = line
                    setattr(cls, attr, "\n".join(lines))
                else:
                    setattr(cls, attr, value)
        return cls

    return decorator


@fix_patterns()
class GenericModelCodeGenerator:
    BODY = """
    {{#decorators}}
    @{{.}}
    {{/decorators}}
    class {{name}}:{{#nested}}
    {{.}}        
    {{/nested}}$
    ${{#fields}}
        {{.}}$
    ${{/fields}}
    """

    FIELD = "{{name}}: {{type}}{{#body}} = {{.}}{{/body}}"

    def __init__(self, model: ModelMeta):
        self.model = model

    @staticmethod
    def indent(string, lvl=1, indent=INDENT):
        return "\n".join(indent * lvl + line for line in string.split("\n"))

    def generate(self, nested_classes: List[str] = None) -> Tuple[ImportPathList, str]:
        imports, fields = self.fields
        data = {
            "decorators": self.decorators,
            "name": self.model.name,
            "fields": fields,
            **({"nested": [self.indent(s) for s in nested_classes]} if nested_classes else {})
        }
        return imports, chevron.render(template=self.BODY, data=data)

    @property
    def decorators(self) -> List[str]:
        return []

    def field_data(self, name: str, meta: MetaData, optional: bool) -> Tuple[ImportPathList, dict]:
        imports, typing = metadata_to_typing(meta)
        data = {
            "name": name,
            "type": typing
        }
        return imports, data

    @property
    def fields(self) -> Tuple[ImportPathList, List[str]]:
        required, optional = sort_fields(self.model)
        imports: ImportPathList = []
        strings: List[str] = []
        for is_optional, fields in enumerate((required, optional)):
            for field in fields:
                field_imports, data = self.field_data(field, self.model.type[field], bool(is_optional))
                imports.extend(field_imports)
                strings.append(chevron.render(template=self.FIELD, data=data))
        return imports, strings


def _generate_code(
        structure: List[dict],
        class_generator: Type[GenericModelCodeGenerator],
        class_generator_kwargs: dict,
        lvl=0
) -> Tuple[ImportPathList, List[str]]:
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
        # noinspection PyArgumentList
        gen = class_generator(data["model"], **class_generator_kwargs)
        cls_imports, cls_string = gen.generate(nested_classes)
        imports.extend(cls_imports)
        classes.append(cls_string)
    return imports, classes


OBJECTS_DELIMITER = "\n" * 3


def generate_code(structure: List[dict], class_generator: Type[GenericModelCodeGenerator],
                  class_generator_kwargs: dict = None) -> str:
    imports, classes = _generate_code(structure, class_generator, class_generator_kwargs or {})
    return compile_imports(imports) + OBJECTS_DELIMITER + OBJECTS_DELIMITER.join(classes) + "\n"
