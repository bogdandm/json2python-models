"""
Path of Exile Stash API http://www.pathofexile.com/developer/docs/api-resource-public-stash-tabs
"""
from datetime import datetime

import requests

from json_to_models.generator import MetadataGenerator
from json_to_models.models.base import generate_code
from json_to_models.models.pydantic import PydanticModelCodeGenerator
from json_to_models.models.structure import compose_models_flat
from json_to_models.registry import ModelRegistry
from testing_tools.real_apis import dump_response


def stash_tabs():
    return requests.get("http://api.pathofexile.com/public-stash-tabs").json()


def main():
    tabs = stash_tabs()
    dump_response("pathofexile", "tabs", tabs)
    tabs = tabs['stashes']

    print(f"Start model generation (data len = {len(tabs)})")
    start_t = datetime.now()
    # register_datetime_classes()
    gen = MetadataGenerator()
    reg = ModelRegistry()
    fields = gen.generate(*tabs)
    reg.process_meta_data(fields, model_name="Tab")
    reg.merge_models(generator=gen)
    reg.generate_names()

    # print("Meta tree:")
    # print(pretty_format_meta(next(iter(reg.models))))
    # print("\n" + "=" * 20, end='')

    structure = compose_models_flat(reg.models_map)
    # print('\n', json_format([structure[0], {str(a): str(b) for a, b in structure[1].items()}]))
    # print("=" * 20)

    print(generate_code(structure, PydanticModelCodeGenerator))
    print(f"{(datetime.now() - start_t).total_seconds():.4f} seconds")


if __name__ == '__main__':
    main()
