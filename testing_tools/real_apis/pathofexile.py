"""
Path of Exile API http://www.pathofexile.com/developer/docs/api-resource-public-stash-tabs
"""
import requests

from rest_client_gen.generator import MetadataGenerator
from rest_client_gen.models import compose_models
from rest_client_gen.models.base import GenericModelCodeGenerator, generate_code
from rest_client_gen.registry import ModelRegistry
from rest_client_gen.utils import json_format
from testing_tools.pprint_meta_data import pretty_format_meta
from testing_tools.real_apis import dump_response


def stash_tabs():
    return requests.get("http://api.pathofexile.com/public-stash-tabs").json()


def main():
    tabs = stash_tabs()
    dump_response("pathofexile", "tabs", tabs)
    tabs = tabs['stashes']

    print(f"Start model generation (data len = {len(tabs)})")
    gen = MetadataGenerator()
    reg = ModelRegistry()
    fields = gen.generate(*tabs)
    reg.process_meta_data(fields, model_name="Tab")
    reg.merge_models(generator=gen)
    reg.generate_names()

    print(pretty_format_meta(next(iter(reg.models))))
    print("\n" + "=" * 20, end='')

    structure = compose_models(reg.models_map)
    print('\n', json_format([structure[0], {str(a): str(b) for a, b in structure[1].items()}]))
    print("=" * 20)

    print(generate_code(structure, GenericModelCodeGenerator))


if __name__ == '__main__':
    main()
