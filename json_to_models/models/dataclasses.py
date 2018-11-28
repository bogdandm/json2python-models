from inspect import isclass
from typing import List, Tuple

from .base import GenericModelCodeGenerator, KWAGRS_TEMPLATE, METADATA_FIELD_NAME, sort_kwargs, template
from ..dynamic_typing import DDict, DList, DOptional, ImportPathList, MetaData, ModelMeta, StringSerializable

DEFAULT_ORDER = (
    ("default", "default_factory"),
    "*",
    ("metadata",)
)


class DataclassModelCodeGenerator(GenericModelCodeGenerator):
    DC_DECORATOR = template("dataclass"
                            "{% if kwargs %}"
                            f"({KWAGRS_TEMPLATE})"
                            "{% endif %}")
    DC_FIELD = template(f"field({KWAGRS_TEMPLATE})")

    def __init__(self, model: ModelMeta, meta=False, post_init_converters=False, dataclass_kwargs: dict = None,
                 **kwargs):
        """
        :param model: ModelMeta instance
        :param meta: Enable generation of metadata as attrib argument
        :param post_init_converters: Enable generation of type converters in __post_init__ methods
        :param dataclass_kwargs: kwargs for @dataclass() decorators
        :param kwargs:
        """
        super().__init__(model, **kwargs)
        self.post_init_converters = post_init_converters
        self.no_meta = not meta
        self.dataclass_kwargs = dataclass_kwargs or {}

    def generate(self, nested_classes: List[str] = None) -> Tuple[ImportPathList, str]:
        """
        :param nested_classes: list of strings that contains classes code
        :return: list of import data, class code
        """
        imports, code = super().generate(nested_classes)
        imports.append(('dataclasses', ['dataclass, field']))
        return imports, code

    @property
    def decorators(self) -> List[str]:
        """
        :return: List of decorators code (without @)
        """
        return [self.DC_DECORATOR.render(kwargs=self.dataclass_kwargs)]

    def field_data(self, name: str, meta: MetaData, optional: bool) -> Tuple[ImportPathList, dict]:
        """
        Form field data for template

        :param name: Field name
        :param meta: Field metadata
        :param optional: Is field optional
        :return: imports, field data
        """
        imports, data = super().field_data(name, meta, optional)
        body_kwargs = {}
        if optional:
            meta: DOptional
            if isinstance(meta.type, DList):
                body_kwargs["default_factory"] = "list"
            elif isinstance(meta.type, DDict):
                body_kwargs["default_factory"] = "dict"
            else:
                body_kwargs["default"] = "None"
                if isclass(meta.type) and issubclass(meta.type, StringSerializable):
                    pass
        elif isclass(meta) and issubclass(meta, StringSerializable):
            pass

        if not self.no_meta:
            body_kwargs["metadata"] = {METADATA_FIELD_NAME: name}
        if len(body_kwargs) == 1 and next(iter(body_kwargs.keys())) == "default":
            data["body"] = body_kwargs["default"]
        elif body_kwargs:
            data["body"] = self.DC_FIELD.render(kwargs=sort_kwargs(body_kwargs, DEFAULT_ORDER))
        return imports, data
