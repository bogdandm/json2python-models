from inspect import isclass
from typing import List, Tuple

from ..dynamic_typing import (
    DDict,
    DList,
    DOptional,
    ImportPathList,
    MetaData,
    ModelMeta,
    StringLiteral,
    StringSerializable,
)
from .base import (
    KWAGRS_TEMPLATE,
    METADATA_FIELD_NAME,
    GenericModelCodeGenerator,
    sort_kwargs,
    template,
)

DEFAULT_ORDER = (("default", "converter", "factory"), "*", ("metadata",))


class AttrsModelCodeGenerator(GenericModelCodeGenerator):
    ATTRS = template(f"attr.s{{% if kwargs %}}({KWAGRS_TEMPLATE}){{% endif %}}")
    ATTRIB = template(f"attr.ib({KWAGRS_TEMPLATE})")
    default_types_style = {
        StringLiteral: {StringLiteral.TypeStyle.use_literals: False}
    }

    def __init__(
        self, model: ModelMeta, meta=False, attrs_kwargs: dict = None, **kwargs
    ):
        """
        :param model: ModelMeta instance
        :param meta: Enable generation of metadata as attrib argument
        :param attrs_kwargs: kwargs for @attr.s() decorators
        :param kwargs:
        """
        super().__init__(model, **kwargs)
        self.no_meta = not meta
        self.attrs_kwargs = attrs_kwargs or {}

    @property
    def decorators(self) -> Tuple[ImportPathList, List[str]]:
        imports, decorators = super().decorators
        imports.append(("attr", None))
        decorators.insert(0, self.ATTRS.render(kwargs=self.attrs_kwargs))
        return imports, decorators

    def field_data(
        self, name: str, meta: MetaData, optional: bool
    ) -> Tuple[ImportPathList, dict]:
        """
        Form field data for template

        :param name: Original field name
        :param meta: Field metadata
        :param optional: Is field optional
        :return: imports, field data
        """
        imports, data = super().field_data(name, meta, optional)
        body_kwargs = {}
        if optional:
            meta: DOptional
            if isinstance(meta.type, DList):
                body_kwargs["factory"] = "list"
            elif isinstance(meta.type, DDict):
                body_kwargs["factory"] = "dict"
            else:
                body_kwargs["default"] = "None"
                if (
                    isclass(meta.type)
                    and issubclass(meta.type, StringSerializable)
                    and not self.post_init_converters
                ):
                    body_kwargs["converter"] = (
                        f"optional({
                            meta.type.__name__})"
                    )
                    imports.append(("attr.converter", "optional"))
        elif (
            isclass(meta)
            and issubclass(meta, StringSerializable)
            and not self.post_init_converters
        ):
            body_kwargs["converter"] = meta.__name__

        if not self.no_meta and name != data["name"]:
            body_kwargs["metadata"] = {METADATA_FIELD_NAME: name}
        data["body"] = self.ATTRIB.render(
            kwargs=sort_kwargs(body_kwargs, DEFAULT_ORDER)
        )
        return imports, data

    @property
    def convert_strings_kwargs(self) -> Tuple[ImportPathList, dict]:
        """
        :return: Imports and Dict with kw-arguments for
        `json_to_models.models.string_converters.convert_strings` decorator.
        """
        imports, kwargs = super().convert_strings_kwargs
        imports.append(("json_to_models.models", ["ClassType"]))
        kwargs["class_type"] = "ClassType.Attrs"
        return imports, kwargs
