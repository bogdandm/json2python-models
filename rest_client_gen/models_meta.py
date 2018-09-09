from typing import List, Optional, Set

import inflection

from .dynamic_typing import MetaData, SingleType

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

    def __str__(self):
        return f"Model#{self.index}" + ("-" + self._name if self._name else "")

    def __eq__(self, other):
        if isinstance(other, dict):
            return self.type == other
        else:
            return super().__eq__(other)

    def __hash__(self):
        return hash(self.index)

    def update_base_name(self):
        # TODO: Tests
        base_names = {singularize(inflection.underscore(ptr.parent_field_name))
                      for ptr in self.pointers if ptr.parent is not None}
        filtered_names = set()
        for name in base_names:
            if filtered_names:
                for other in list(filtered_names):
                    if name in other:
                        filtered_names.add(name)
                        filtered_names.remove(other)
                        break
                    elif other in name:
                        break
                    else:
                        filtered_names.add(name)
            else:
                filtered_names.add(name)
        names = [inflection.camelize(name)
                 for name in sorted(filtered_names)]
        self._name = "_".join(names)

    @property
    def base_name(self) -> str:
        if self._name is None:
            self.update_base_name()
        return self._name

    @base_name.setter
    def base_name(self, value: str):
        self._name = value

    @base_name.deleter
    def base_name(self):
        self._name = None

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
