from random import shuffle

import pytest
from inflection import singularize

from json_to_models.utils import distinct_words, json_format

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
