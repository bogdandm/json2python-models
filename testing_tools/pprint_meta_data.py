from inspect import isclass

from rest_client_gen.dynamic_typing import SingleType, ComplexType, StringSerializable
from rest_client_gen.generator import Generator
from testing_tools.data import test_data
from rest_client_gen.registry import ModelRegistry, ModelMeta


def pprint_gen(value, key=None, lvl=0, empty_line=True):
    if empty_line:
        yield "\n"
        if lvl > 0:
            yield '\t' * lvl
    else:
        print(end=' ')
    if key is not None:
        yield f"{key} -> "

    if isinstance(value, dict):
        yield "object:"
        for key, value in value.items():
            yield from pprint_gen(value, key, lvl=lvl + 1)

    elif isinstance(value, list):
        for t in value:
            yield from pprint_gen(t, lvl=lvl + 1)
        # raise ValueError(value)

    elif isinstance(value, ModelMeta):
        yield f"Model#{value.index}:"
        for key, value in value.type.items():
            yield from pprint_gen(value, key, lvl=lvl + 1)

    elif isinstance(value, SingleType):
        yield f"{value.__class__.__name__}:"
        yield from pprint_gen(value.type, lvl=lvl, empty_line=False)

    elif isinstance(value, ComplexType):
        yield f"{value.__class__.__name__}:"

        for t in value.types:
            yield from pprint_gen(t, lvl=lvl + 1)

    elif isclass(value) and issubclass(value, StringSerializable):
        yield f"(type=<class '{value.__name__}'>)"

    else:
        yield f"(type={getattr(value, 'type', value)})"


if __name__ == '__main__':
    gen = Generator()
    reg = ModelRegistry()
    fields = gen.generate(*test_data)
    model = reg.process_meta_data(fields)
    for s in pprint_gen(model):
        print(s, end='')
    print('\n' + '-' * 10, end='')
