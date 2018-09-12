from typing import List, Optional, Set, Tuple

import inflection

from .base import ImportPathList, MetaData, SingleType
from ..utils import distinct_words

try:
    # https://www.clips.uantwerpen.be/pages/pattern-en#pluralization
    from pattern.text.en import singularize
except ImportError:
    try:
        # https://www.nodebox.net/code/index.php/Linguistics#pluralization
        from en.noun import singular as singularize
    except ImportError:
        def singularize(word: str) -> str:
            if word.endswith('ies'):
                return word[:-3] + "y"
            if word.endswith('s'):
                return word[:-1]
            return word


class ModelMeta(SingleType):
    def __init__(self, t: MetaData, index, _original_fields=None):
        super().__init__(t)
        self.original_fields: List[List[str]] = _original_fields or [list(self.type.keys())]
        self.index = index
        self.pointers: Set[ModelPtr] = set()
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
        # TODO: Tests
        base_names = (singularize(inflection.underscore(ptr.parent_field_name))
                      for ptr in self.pointers if ptr.parent is not None)
        filtered_names = distinct_words(*base_names)
        new_name = self.name_joiner(*map(inflection.camelize, sorted(filtered_names)))
        if new_name:
            self._name = new_name
            self._name_generated = True

    @classmethod
    def name_joiner(cls, *names: str) -> str:
        return "_".join(names)

    @property
    def name(self) -> str:
        # if self._name is None:
        #     self.generate_name()
        return self._name

    @name.setter
    def name(self, name: str):
        value = inflection.camelize(singularize(name))
        self._name = value
        self._name_generated = False

    @name.deleter
    def name(self):
        self._name = None

    def set_raw_name(self, name):
        self._name = name
        self._name_generated = False

    @property
    def is_name_generated(self):
        return self._name_generated

    def connect(self, ptr: 'ModelPtr'):
        self.pointers.add(ptr)

    def disconnect(self, ptr: 'ModelPtr'):
        self.pointers.remove(ptr)

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

    def __hash__(self):
        return id(self)

    def replace(self, t: ModelMeta, **kwargs):
        self.type.disconnect(self)
        super().replace(t, **kwargs)
        self.type.connect(self)

    def to_typing_code(self) -> Tuple[ImportPathList, str]:
        imports, model = self.type.to_typing_code()
        return imports, f"'{model}'"
