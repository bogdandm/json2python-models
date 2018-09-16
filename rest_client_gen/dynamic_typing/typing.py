import operator
from collections import OrderedDict
from inspect import isclass
from typing import Dict, Set, Tuple

from .base import ImportPathList, MetaData
from .string_serializable import StringSerializable


def metadata_to_typing(t: MetaData) -> Tuple[ImportPathList, str]:
    if isclass(t):
        if issubclass(t, StringSerializable):
            return t.to_typing_code()
        else:
            return ([], t.__name__)
    elif isinstance(t, dict):
        raise ValueError("Can not convert dict instance to typing code. It should be wrapped into ModelMeta instance")
    else:
        return t.to_typing_code()


def compile_imports(imports: ImportPathList) -> str:
    imports_map: Dict[str, Set[str]] = OrderedDict()
    for module, classes in filter(None, imports):
        classes_set = imports_map.get(module, set())
        if isinstance(classes, str):
            classes_set.add(classes)
        else:
            classes_set.update(classes)
        imports_map[module] = classes_set

    imports_map = OrderedDict(sorted(
        ((module, sorted(classes)) for module, classes in imports_map.items()),
        key=operator.itemgetter(0)
    ))

    imports_map_joined = OrderedDict()
    for module, classes in imports_map.items():
        imports_map_joined[module] = ", ".join(classes)

    return "\n".join(f"from {module} import {classes}" for module, classes in imports_map_joined.items())
