from typing import List, Optional, Tuple

from .base import GenericModelCodeGenerator, KWAGRS_TEMPLATE, sort_kwargs, template
from ..dynamic_typing import (
    DDict,
    DList,
    DOptional,
    ImportPathList,
    MetaData,
    ModelMeta,
    Null,
    StringLiteral,
    StringSerializable,
    Unknown
)

DEFAULT_ORDER = (
    "*",
)


class PydanticModelCodeGenerator(GenericModelCodeGenerator):
    PYDANTIC_FIELD = template("Field({{ default }}{% if kwargs %}, KWAGRS_TEMPLATE{% endif %})"
                              .replace('KWAGRS_TEMPLATE', KWAGRS_TEMPLATE))
    default_types_style = {
        StringSerializable: {
            StringSerializable.TypeStyle.use_actual_type: True
        },
        StringLiteral: {
            StringLiteral.TypeStyle.use_literals: True
        }
    }

    def __init__(self, model: ModelMeta, **kwargs):
        """
        :param model: ModelMeta instance
        :param kwargs:
        """
        kwargs['post_init_converters'] = False
        super().__init__(model, **kwargs)

    def generate(self, nested_classes: List[str] = None, extra: str = "", **kwargs) \
            -> Tuple[ImportPathList, str]:
        imports, body = super(PydanticModelCodeGenerator, self).generate(
            bases='BaseModel',
            nested_classes=nested_classes,
            extra=extra
        )
        imports.append(('pydantic', ['BaseModel', 'Field']))
        return imports, body

    def _filter_fields(self, fields):
        fields = super()._filter_fields(fields)
        filtered = []
        for field in fields:
            field_type = self.model.type[field]
            if field_type in (Unknown, Null):
                continue
            filtered.append(field)
        return filtered

    def field_data(self, name: str, meta: MetaData, optional: bool) -> Tuple[ImportPathList, dict]:
        """
        Form field data for template

        :param name: Original field name
        :param meta: Field metadata
        :param optional: Is field optional
        :return: imports, field data
        """
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
