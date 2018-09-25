import operator
from collections import OrderedDict
from inspect import isclass
from typing import Dict, Set, Tuple

from rest_client_gen.lazy import keep_lazy
from .base import ImportPathList, MetaData
from .string_serializable import StringSerializable


@keep_lazy(tuple)
def metadata_to_typing(t: MetaData) -> Tuple[ImportPathList, str]:
    """
    Shortcut function to call ``to_typing_code`` method of BaseType instances or return name of type otherwise
    :param t:
    :return:
    """
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
    """
    Merge list of imports path and convert them into list code (string)
    """
    imports_map: Dict[str, Set[str]] = OrderedDict()
    for module, classes in filter(None, imports):
        classes_set = imports_map.get(module, set())
        if isinstance(classes, str):
            classes_set.add(classes)
        else:
            classes_set.update(classes)
        imports_map[module] = classes_set

    # Sort imports by package name and sort class names of each import
    imports_map = OrderedDict(sorted(
        ((module, sorted(classes)) for module, classes in imports_map.items()),
        key=operator.itemgetter(0)
    ))

    return "\n".join(f"from {module} import {', '.join(classes)}" for module, classes in imports_map.items())
