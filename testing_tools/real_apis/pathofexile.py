"""
Path of Exile API http://www.pathofexile.com/developer/docs/api-resource-public-stash-tabs
"""
import requests

from rest_client_gen.generator import MetadataGenerator
from rest_client_gen.registry import ModelRegistry
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

    model = reg.process_meta_data(fields)
    print(pretty_format_meta(model))
    print('\n' + '-' * 10, end='')

    result = reg.merge_models(generator=gen)
    for model, group in result:
        print("\n" + "=" * 20, end='')
        print(pretty_format_meta(model))

        print("\n" + "-" * 10 + " replaces " + "-" * 10, end='')
        for old_model in group:
            print(pretty_format_meta(old_model))

    print("\n" + "=" * 20, end='')
    for model in reg.models:
        model.generate_name()
    print(pretty_format_meta(next(iter(reg.models))))


if __name__ == '__main__':
    main()
