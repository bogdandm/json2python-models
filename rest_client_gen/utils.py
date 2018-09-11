import json
from typing import Set


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
        for other in list(filtered_words):
            if name in other:
                filtered_words.add(name)
                filtered_words.remove(other)
                break
            elif other in name:
                break
        else:
            filtered_words.add(name)
    return filtered_words
