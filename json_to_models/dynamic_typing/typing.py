import operator
from inspect import isclass
from typing import Dict, Set, Tuple

from .base import ImportPathList, MetaData
from .string_serializable import StringSerializable


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
    class_imports_map: Dict[str, Set[str]] = {}
    package_imports_set: Set[str] = set()
    for module, classes in filter(None, imports):
        if classes is None:
            package_imports_set.add(module)
        else:
            classes_set = class_imports_map.get(module, set())
            if isinstance(classes, str):
                classes_set.add(classes)
            else:
                classes_set.update(classes)
            class_imports_map[module] = classes_set

    # Sort imports by package name and sort class names of each import
    class_imports_map = dict(sorted(
        ((module, sorted(classes)) for module, classes in class_imports_map.items()),
        key=operator.itemgetter(0)
    ))

    class_imports = "\n".join(
        f"from {module} import {', '.join(classes)}"
        for module, classes in class_imports_map.items()
    )
    package_imports = "\n".join(
        f"import {module}"
        for module in sorted(package_imports_set)
    )
    return "\n".join(filter(None, (package_imports, class_imports)))
