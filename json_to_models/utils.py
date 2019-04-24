import json
from functools import wraps
from typing import Callable, Optional, Set


class Index:
    def __init__(self):
        self.ch = 'A'
        self.i = 1

    def __call__(self, *args, **kwargs):
        value = '%i%s' % (self.i, self.ch)
        ch = chr(ord(self.ch) + 1)
        if ch <= 'Z':
            self.ch = ch
        else:
            self.ch = 'A'
            self.i += 1
        return value


def json_format(x) -> str:
    return json.dumps(x, indent=4, default=str, ensure_ascii=False)


def distinct_words(*words: str) -> Set[str]:
    """
    Filters strings so only unique strings without extended ones will be exists in resulted set, e.g.
    >>> distinct_words('test', 'another_test', 'foo', 'qwerty_foo_bar')
    {'test', 'foo'}

    :param words:
    :return:
    """
    words = set(words)
    filtered_words = set()
    for name in words:
        flag = True
        for other in list(filtered_words):
            if name in other:
                filtered_words.add(name)
                filtered_words.remove(other)
                flag = False
            elif other in name:
                flag = False
        if flag:
            filtered_words.add(name)
    return filtered_words


def convert_args(fn: Callable, *args_converters: Optional[type], **kwargs_converters: Optional[type]) -> Callable:
    """
    Decorator. Apply ``args_converters`` to callable arguments and kwargs_converters to kwargs.
    If converter is None then argument will passed as is.

    :param fn: Function or class
    :param args_converters: Arguments converters
    :param kwargs_converters: Keyword arguments converters
    :return: Callable wrapper
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        converted = (
            t(value) if t else value
            for value, t in zip(args, args_converters)
        )
        kwargs_converted = {
            name: kwargs_converters[name](kwargs[name]) if kwargs_converters.get(name, None) else kwargs[name]
            for name in kwargs.keys()
        }
        if len(args_converters) < len(args):
            remain = args[len(args_converters):]
        else:
            remain = ()
        return fn(*converted, *remain, **kwargs_converted)

    return wrapper


def convert_args_decorator(*args_converters: type, method=False, **kwargs_converters):
    """
    Decorator factory.

    :param args_converters: Arguments converters
    :param method: Set to True if decorated function is method or classmethod
    :param kwargs_converters: Keyword arguments converters
    :return:
    """

    def decorator(fn):
        if method:
            return convert_args(fn, None, *args_converters, **kwargs_converters)
        else:
            return convert_args(fn, *args_converters, **kwargs_converters)

    return decorator


def cached_method(func: Callable):
    """
    Decorator to cache method return values
    """
    null = object()

    @wraps(func)
    def cached_fn(self, *args):
        if getattr(self, '__cache__', None) is None:
            setattr(self, '__cache__', {})
        value = self.__cache__.get(args, null)
        if value is null:
            value = func(self, *args)
            self.__cache__[args] = value
        return value

    return cached_fn


def cached_classmethod(func: Callable):
    """
    Decorator to cache classmethod return values
    """
    cache = {}
    null = object()

    @wraps(func)
    def cached_fn(cls, *args):
        value = cache.get(args, null)
        if value is null:
            value = func(cls, *args)
            cache[args] = value
        return value

    return classmethod(cached_fn)
