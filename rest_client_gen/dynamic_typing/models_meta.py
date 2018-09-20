from typing import List, Optional, Set, Tuple

import inflection

from .base import ImportPathList, MetaData
from .complex import SingleType
from ..utils import distinct_words


class ModelMeta(SingleType):
    WORDS_SEPARATOR = "_"

    def __init__(self, t: MetaData, index, _original_fields=None):
        super().__init__(t)
        self.original_fields: List[List[str]] = _original_fields or [list(self.type.keys())]
        self.index: str = index
        self.pointers: Set[ModelPtr] = set()
        self.child_pointers: Set[ModelPtr] = set()  # parent ref (pointers that have ptr.parent == self)
        self._name: Optional[str] = None
        self._name_generated: Optional[bool] = None

    def __str__(self):
        return f"Model#{self.index}" + ("-" + self._name if self._name else "")

    def __eq__(self, other):
        if isinstance(other, dict):
            return self.type == other
        else:
            return super().__eq__(other)

    def __hash__(self):
        return hash(self.index)

    def generate_name(self):
        """
        Generate model name based on fields to which his model is assigned.
        Will overwrite existed name so check is_name_generated before call this method
        """
        base_names = (inflection.singularize(inflection.underscore(ptr.parent_field_name))
                      for ptr in self.pointers if ptr.parent is not None)
        filtered_names = distinct_words(*base_names)
        new_name = self.name_joiner(*map(inflection.camelize, sorted(filtered_names)))
        if new_name:
            self._name = new_name
            self._name_generated = True

    @classmethod
    def name_joiner(cls, *names: str) -> str:
        """
        Join words to form a model name. Uses in different places so override WORDS_SEPARATOR to change it globally.
        """
        return cls.WORDS_SEPARATOR.join(names)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str):
        """
        Convert given name to singular form and CamelCase format
        """
        self._name = inflection.camelize(inflection.singularize(name))
        self._name_generated = False

    @name.deleter
    def name(self):
        self._name = None

    def set_raw_name(self, name, generated=False):
        """
        Set model name and is_name_generated flag as is without any conversion made
        """
        self._name = name
        self._name_generated = generated

    @property
    def is_name_generated(self):
        return self._name_generated

    def connect(self, ptr: 'ModelPtr'):
        self.pointers.add(ptr)

    def disconnect(self, ptr: 'ModelPtr'):
        self.pointers.remove(ptr)

    def add_child_ref(self, ptr: 'ModelPtr'):
        self.child_pointers.add(ptr)

    def remove_child_ref(self, ptr: 'ModelPtr'):
        self.child_pointers.remove(ptr)

    def to_typing_code(self) -> Tuple[ImportPathList, str]:
        if self.name is None:
            raise ValueError('Model without name can not be typed')
        return [], self.name


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
        if parent:
            parent.add_child_ref(self)

    def __hash__(self):
        return id(self)

    def replace(self, t: ModelMeta, **kwargs) -> 'ModelPtr':
        self.type.disconnect(self)
        super().replace(t, **kwargs)
        self.type.connect(self)
        return self

    def replace_parent(self, t: ModelMeta, **kwargs) -> 'ModelPtr':
        self.parent.remove_child_ref(self)
        self.parent = t
        self.parent.add_child_ref(self)
        return self

    def to_typing_code(self) -> Tuple[ImportPathList, str]:
        imports, model = self.type.to_typing_code()
        return imports, f"'{model}'"
