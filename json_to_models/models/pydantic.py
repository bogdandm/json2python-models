from typing import List, Tuple

from .base import GenericModelCodeGenerator, KWAGRS_TEMPLATE, sort_kwargs, template
from ..dynamic_typing import DDict, DList, DOptional, ImportPathList, MetaData, ModelMeta

DEFAULT_ORDER = (
    "*",
)


class PydanticModelCodeGenerator(GenericModelCodeGenerator):
    PYDANTIC_FIELD = template("Field({{ default }}{% if kwargs %}, KWAGRS_TEMPLATE{% endif %})"
                              .replace('KWAGRS_TEMPLATE', KWAGRS_TEMPLATE))

    def __init__(self, model: ModelMeta, attrs_kwargs: dict = None,
                 convert_unicode=True):
        """
        :param model: ModelMeta instance
        :param meta: Enable generation of metadata as attrib argument
        :param post_init_converters: Enable generation of type converters in __post_init__ methods
        :param attrs_kwargs: kwargs for @attr.s() decorators
        :param kwargs:
        """
        super().__init__(model, post_init_converters=False, convert_unicode=convert_unicode)
        self.attrs_kwargs = attrs_kwargs or {}

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
        imports, data = super().field_data(name, meta, optional)
        default = '...'
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
            data["body"] = self.PYDANTIC_FIELD.render(default=default, kwargs=sort_kwargs(body_kwargs, DEFAULT_ORDER))
        elif default != '...':
            data["body"] = default
        return imports, data
