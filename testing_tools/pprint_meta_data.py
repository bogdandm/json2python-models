from inspect import isclass

from rest_client_gen.dynamic_typing import ComplexType, ModelMeta, ModelPtr, SingleType, StringSerializable
from rest_client_gen.generator import MetadataGenerator
from rest_client_gen.registry import ModelRegistry
from testing_tools.data import test_data


def _pprint_gen(value, key=None, lvl=0, empty_line=True, ignore_ptr=False):
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
            yield from _pprint_gen(value, key, lvl=lvl + 1, ignore_ptr=ignore_ptr)

    elif isinstance(value, list):
        for t in value:
            yield from _pprint_gen(t, lvl=lvl + 1, ignore_ptr=ignore_ptr)
        # raise ValueError(value)

    elif ignore_ptr and isinstance(value, ModelPtr):
        yield f"Model#{value.type.index}: ..."

    elif isinstance(value, ModelMeta):
        yield str(value) + ":"
        for key, subvalue in value.type.items():
            yield from _pprint_gen(subvalue, key, lvl=lvl + 1, ignore_ptr=ignore_ptr)
        if not value.type:
            yield " <empty>"

    elif isinstance(value, SingleType):
        yield f"{value.__class__.__name__}:"
        yield from _pprint_gen(value.type, lvl=lvl, empty_line=False, ignore_ptr=ignore_ptr)

    elif isinstance(value, ComplexType):
        yield f"{value.__class__.__name__}:"

        for t in value.types:
            yield from _pprint_gen(t, lvl=lvl + 1, ignore_ptr=ignore_ptr)

    elif isclass(value) and issubclass(value, StringSerializable):
        yield f"(type=<class '{value.__name__}'>)"

    else:
        yield f"(type={getattr(value, 'type', value)})"


def pretty_format_meta(value, ignore_ptr=False):
    return "".join(_pprint_gen(value, ignore_ptr=ignore_ptr))


if __name__ == '__main__':
    gen = MetadataGenerator()
    reg = ModelRegistry()
    fields = gen.generate(*test_data)
    model = reg.process_meta_data(fields)
    print(pretty_format_meta(model))
    print('\n' + '-' * 10, end='')

    reg.merge_models(generator=gen)
    for model in reg.models:
        print(pretty_format_meta(model, ignore_ptr=True))
