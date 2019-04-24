from random import shuffle

import pytest
from inflection import singularize

from json_to_models.utils import (Index, cached_classmethod, cached_method, convert_args_decorator, distinct_words,
                                  json_format)

test_distinct_words_data = [
    pytest.param(['test', 'foo', 'bar'], {'test', 'foo', 'bar'}),
    pytest.param(['test', 'foo', 'bar', 'foo_bar'], {'test', 'foo', 'bar'}),
    pytest.param(['awesome_asdawdaw', 'awesome_testing', 'test', 'simple_test', 'awesome'], {'test', 'awesome'}),
    pytest.param(['awesome_testing', 'test'], {'test'}),
]


@pytest.mark.parametrize("value,expected", test_distinct_words_data)
def test_distinct_words(value, expected):
    shuffled = value[:]
    shuffle(shuffled)
    for v in (value, reversed(value), shuffled):
        v = list(v)
        words_set = distinct_words(*v)
        assert words_set == expected, f"Test case: {v}"


def test_json_format():
    d = {'a': 2, 'aswr': [*range(10)]}
    d['d'] = d.copy()
    s = json_format(d)
    print(s)
    assert '\n' in s
    assert ' ' * 4 in s


def test_singularize():
    data = {
        'dogs': 'dog',
        'properties': 'property',
        'cat': 'cat'
    }
    for plur, sing in data.items():
        assert singularize(plur) == sing


def test_index():
    ix = Index()
    for _ in range(1000):
        ix()


@convert_args_decorator(int, b=float)
def f(a, b):
    return a + b


class A:
    @convert_args_decorator(float, float, method=True)
    def __init__(self, x, y):
        self.value = x + y


def test_convert_args_decorator():
    assert f('1', b='1.5') == 2.5
    a = A("2.3", "7.5")
    assert a.value == 9.8


def test_cached_methods():
    class A:
        x = []

        def __init__(self):
            self.y = []

        @cached_method
        def f(self, a):
            self.y.append(a)
            return a

        @cached_classmethod
        def g(cls, a):
            cls.x.append(a)
            return a

    A.g('a')
    A.g('a')
    a = A()
    A.g('b')
    A.g('a')
    a.f('b')
    a.f('b')
    a.f('a')
    a.f('a')
    b = A()
    a.f('b')
    b.f('a')
    b.g('c')

    assert A.x == ['a', 'b', 'c']
    assert a.y == ['b', 'a']
    assert b.y == ['a']
    assert a.x == ['a', 'b', 'c']
