from typing import List, Set

from .dynamic_typing import SingleType, MetaData


class ModelMeta(SingleType):
    def __init__(self, t: MetaData, index, _original_fields=None):
        super().__init__(t)
        self.original_fields: List[List[str]] = _original_fields or [list(self.type.keys())]
        self.index = index
        self.pointers: Set[ModelPtr] = set()

    def __str__(self):
        return f"Model#{self.index}"

    def __eq__(self, other):
        if isinstance(other, dict):
            return self.type == other
        else:
            return super().__eq__(other)

    def __hash__(self):
        return hash(self.index)

    def connect(self, ptr: 'ModelPtr'):
        self.pointers.add(ptr)

    def disconnect(self, ptr: 'ModelPtr'):
        self.pointers.remove(ptr)


class ModelPtr(SingleType):
    """
    Model wrapper (pointer)
    """
    type: ModelMeta

    def __init__(self, meta: ModelMeta, parent: ModelMeta = None, parent_field_name: str = None):
        super().__init__(meta)
        self.parent = parent
        self.parent_field_name = parent_field_name
        meta.connect(self)

    def __hash__(self):
        return id(self)

    def replace(self, t: ModelMeta, **kwargs):
        self.type.disconnect(self)
        super().replace(t, **kwargs)
        self.type.connect(self)