from inspect import isclass
from typing import List, Optional, Tuple

from .base import GenericModelCodeGenerator, KWAGRS_TEMPLATE, sort_kwargs, template
from ..dynamic_typing import BaseType, DDict, DList, DOptional, ImportPathList, MetaData, ModelMeta, StringSerializable

DEFAULT_ORDER = (
    "*",
)


class PydanticModelCodeGenerator(GenericModelCodeGenerator):
    PYDANTIC_FIELD = template("Field({{ default }}{% if kwargs %}, KWAGRS_TEMPLATE{% endif %})"
                              .replace('KWAGRS_TEMPLATE', KWAGRS_TEMPLATE))

    def __init__(self, model: ModelMeta, convert_unicode=True):
        """
        :param model: ModelMeta instance
        :param meta: Enable generation of metadata as attrib argument
        :param post_init_converters: Enable generation of type converters in __post_init__ methods
        :param kwargs:
        """
        super().__init__(model, post_init_converters=False, convert_unicode=convert_unicode)

    def generate(self, nested_classes: List[str] = None, extra: str = "", **kwargs) \
            -> Tuple[ImportPathList, str]:
        imports, body = super(PydanticModelCodeGenerator, self).generate(
            bases='BaseModel',
            nested_classes=nested_classes,
            extra=extra
        )
        imports.append(('pydantic', ['BaseModel', 'Field']))
        return imports, body

    def field_data(self, name: str, meta: MetaData, optional: bool) -> Tuple[ImportPathList, dict]:
        """
        Form field data for template

        :param name: Original field name
        :param meta: Field metadata
        :param optional: Is field optional
        :return: imports, field data
        """
        _, meta = self.replace_string_serializable(meta)
        imports, data = super().field_data(name, meta, optional)
        default: Optional[str] = None
        body_kwargs = {}
        if optional:
            meta: DOptional
            if isinstance(meta.type, DList):
                default = "[]"
            elif isinstance(meta.type, DDict):
                default = "{}"
            else:
                default = "None"

        if name != data["name"]:
            body_kwargs["alias"] = f'"{name}"'
        if body_kwargs:
            data["body"] = self.PYDANTIC_FIELD.render(
                default=default or '...',
                kwargs=sort_kwargs(body_kwargs, DEFAULT_ORDER)
            )
        elif default is not None:
            data["body"] = default
        return imports, data

    def replace_string_serializable(self, t: MetaData) -> Tuple[bool, MetaData]:
        if isclass(t) and issubclass(t, StringSerializable):
            return True, t.actual_type
        elif isinstance(t, BaseType):
            for i, sub_type in enumerate(t):
                replaced, new_type = self.replace_string_serializable(sub_type)
                if replaced:
                    t.replace(new_type, index=i)
        return False, t
