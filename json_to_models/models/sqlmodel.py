from typing import List, Tuple

from json_to_models.dynamic_typing import ImportPathList, MetaData
from json_to_models.models.base import GenericModelCodeGenerator
from json_to_models.models.pydantic import PydanticModelCodeGenerator


class SqlModelCodeGenerator(PydanticModelCodeGenerator):
    def generate(self, nested_classes: List[str] = None, extra: str = "", **kwargs) \
            -> Tuple[ImportPathList, str]:
        imports, body = GenericModelCodeGenerator.generate(
            self,
            bases='SQLModel, table=True',
            nested_classes=nested_classes,
            extra=extra
        )
        imports.append(('sqlmodel', ['SQLModel', 'Field']))
        body = """
        # Warn! This generated code does not respect SQLModel Relationship and foreign_key, please add them manually.
        """.strip() + '\n' + body
        return imports, body

    def convert_field_name(self, name):
        if name in ('id', 'pk'):
            return name
        return super().convert_field_name(name)

    def _get_field_kwargs(self, name: str, meta: MetaData, optional: bool, data: dict):
        kwargs = super()._get_field_kwargs(name, meta, optional, data)
        # Detect primary key
        if data['name'] in ('id', 'pk') and meta is int:
            kwargs['primary_key'] = True
        return kwargs
