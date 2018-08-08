from typing import Union


def is_optional(t: type) -> bool:
    return getattr(t, '__origin__', None) is Union and isinstance(None, t.__args__[-1])
