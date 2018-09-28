import operator
from inspect import isclass
from typing import List, Tuple

from .base import GenericModelCodeGenerator, template
from ..dynamic_typing import DList, DOptional, ImportPathList, MetaData, ModelMeta, StringSerializable

METADATA_FIELD_NAME = "RCG_ORIGINAL_FIELD"
KWAGRS_TEMPLATE = "{% for key, value in kwargs.items() %}" \
                  "{{ key }}={{ value }}" \
                  "{% if not loop.last %}, {% endif %}" \
                  "{% endfor %}"


def sort_kwargs(kwargs: dict) -> dict:
    # TODO: Unify this function
    meta = kwargs.pop("metadata", {})
    sorted_dict = dict(sorted(kwargs.items(), key=operator.itemgetter(0)))
    if meta:
        sorted_dict["metadata"] = meta
    return sorted_dict


class AttrsModelCodeGenerator(GenericModelCodeGenerator):
    ATTRS = template("attr.s"
                     "{% if kwargs %}"
                     f"({KWAGRS_TEMPLATE})"
                     "{% endif %}")
    ATTRIB = template(f"attr.ib({KWAGRS_TEMPLATE})")

    def __init__(self, model: ModelMeta, no_meta=False, attrs_kwargs: dict = None, **kwargs):
        """
        :param model: ModelMeta instance
        :param no_meta: Disable generation of metadata as attrib argument
        :param attrs_kwargs: kwargs for @attr.s() decorators
        :param kwargs:
        """
        super().__init__(model, **kwargs)
        self.no_meta = no_meta
        self.attrs_kwargs = attrs_kwargs or {}

    def generate(self, nested_classes: List[str] = None) -> Tuple[ImportPathList, str]:
        """
        :param nested_classes: list of strings that contains classes code
        :return: list of import data, class code
        """
        imports, code = super().generate(nested_classes)
        imports.append(('attr', None))
        return imports, code

    @property
    def decorators(self) -> List[str]:
        """
        :return: List of decorators code (without @)
        """
        return [self.ATTRS.render(kwargs=sort_kwargs(self.attrs_kwargs))]

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
                body_kwargs["factory"] = "list"
            else:
                body_kwargs["default"] = "None"
        if isclass(meta) and issubclass(meta, StringSerializable):
            body_kwargs["converter"] = meta.__name__
        if not self.no_meta:
            body_kwargs["metadata"] = {METADATA_FIELD_NAME: name}
        data["body"] = self.ATTRIB.render(kwargs=sort_kwargs(body_kwargs))
        return imports, data
