from collections import OrderedDict
from inspect import isclass
from typing import Dict

from .dynamic_typing import BaseType, SingleType, MetaData
from .utils import Index


class ModelMeta(SingleType):
    def __init__(self, t: MetaData, index):
        super().__init__(t)
        self.index = index
        # TODO: Test pointers
        self.pointers = set()

    def __str__(self):
        return f"Model#{self.index}"

    def __eq__(self, other):
        if isinstance(other, dict):
            return self.type == other
        else:
            return super().__eq__(other)

    def connect(self, ptr: 'ModelPtr'):
        self.pointers.add(ptr)

    def disconnect(self, ptr: 'ModelPtr'):
        self.pointers.remove(ptr)


class ModelPtr(SingleType):
    """
    Model wrapper (pointer)
    """
    type: ModelMeta

    def __init__(self, meta: ModelMeta):
        super().__init__(meta)
        meta.connect(self)

    def __hash__(self):
        return id(self)


class ModelRegistry:
    def __init__(self, k=.7, n=10):
        """

        :param k: Required percent of fields to merge models
        :param n: Required number of fields to merge models
        """
        self.k = k
        self.n = n
        self._registry: Dict[str, ModelMeta] = OrderedDict()
        self._index = Index()

    @property
    def models(self):
        return self._registry.values()

    @property
    def models_map(self):
        return self._registry

    def process_meta_data(self, meta: MetaData, parent: MetaData = None, **kwargs):
        ptr = None
        if isinstance(meta, dict):
            model_meta = self.register(meta)
            ptr = ModelPtr(model_meta)
            if parent:
                parent.replace(ptr, **kwargs)
        if not isclass(meta):
            self._process_nested_meta_data(meta)
        return ptr

    def _process_nested_meta_data(self, meta: MetaData):
        if isinstance(meta, BaseType):
            for i, nested_meta in enumerate(meta):
                self.process_meta_data(nested_meta, parent=meta, index=i)
        elif isinstance(meta, dict):
            for key, value in meta.items():
                ptr = self.process_meta_data(value)
                if ptr:
                    meta[key] = ptr

    def register(self, meta: MetaData):
        model_meta = ModelMeta(meta, self._index())
        self._registry[model_meta.index] = model_meta
        return model_meta

    # def get_similar(self, model_meta: ModelMeta):
    #     # noinspection PyDataclass
    #     fields = attr.fields(model_meta.model)
    #     field_names = {f.name for f in fields}
    #     for m in self.registry:
    #         # noinspection PyDataclass
    #         existing_fields = attr.fields(m.model)
    #         existing_field_names = {f.name for f in existing_fields}
    #         name_intersection = field_names & existing_field_names
    #         name_intersection_len = len(name_intersection)
    #
    #         if (
    #                 name_intersection_len > self.n or
    #                 name_intersection_len / max(len(field_names), len(existing_field_names)) > self.k
    #         ):
    #             yield m
