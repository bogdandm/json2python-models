from collections import OrderedDict
from typing import Dict

from .dynamic_typing import BaseType, MetaData, SingleType
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

    def __init__(self, meta: ModelMeta, parent: ModelMeta = None):
        super().__init__(meta)
        self.parent = parent
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

    def process_meta_data(
            self, meta: MetaData,
            parent: MetaData = None,
            parent_model: ModelMeta = None,
            replace_kwargs=None
    ):
        replace_kwargs = replace_kwargs or {}
        ptr = None

        if isinstance(meta, dict):
            # Register model
            model_meta = self._register(meta)
            ptr = ModelPtr(model_meta, parent=parent_model)
            if parent:
                parent.replace(ptr, **replace_kwargs)

            # Process nested data
            for key, value in meta.items():
                nested_ptr = self.process_meta_data(value, parent_model=model_meta)
                if nested_ptr:
                    meta[key] = nested_ptr

        elif isinstance(meta, BaseType):
            # Process other non-atomic types
            try:
                meta_iter = iter(meta)
            except TypeError:
                pass
            else:
                for i, nested_meta in enumerate(meta_iter):
                    self.process_meta_data(
                        nested_meta,
                        parent=meta,
                        parent_model=parent_model,
                        replace_kwargs={'parent': meta, 'index': i}
                    )

        return ptr

    def _register(self, meta: MetaData):
        model_meta = ModelMeta(meta, self._index())
        self._registry[model_meta.index] = model_meta
        return model_meta
