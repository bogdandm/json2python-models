import json


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