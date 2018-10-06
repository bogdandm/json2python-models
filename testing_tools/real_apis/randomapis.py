"""
Example uses the following APIs:
- CHRONICLING API (https://chroniclingamerica.loc.gov/about/api/)
- Launch Library Reading API (https://launchlibrary.net/docs/1.3/api.html)
"""
import requests

from json_to_models.generator import MetadataGenerator
from json_to_models.registry import ModelRegistry
from testing_tools.pprint_meta_data import pretty_format_meta
from testing_tools.real_apis import dump_response


def chroniclingamerica(tag="michigan"):
    return requests.get(f"http://chroniclingamerica.loc.gov/search/titles/results/?terms={tag}&format=json").json()


def launchlibrary(mission_name="GPS"):
    return requests.get(f"https://launchlibrary.net/1.3/mission/{mission_name}").json()


def main():
    chroniclingamerica_data = chroniclingamerica()
    dump_response("other", "chroniclingamerica", chroniclingamerica_data)

    launchlibrary_data = launchlibrary()
    dump_response("other", "launchlibrary", launchlibrary_data)

    gen = MetadataGenerator()
    reg = ModelRegistry()
    for data in ([chroniclingamerica_data], [launchlibrary_data]):
        fields = gen.generate(*data)

        print(pretty_format_meta(fields))
        print('-' * 10)

        model = reg.process_meta_data(fields)
        print(pretty_format_meta(model))
        print('-' * 10)


if __name__ == '__main__':
    main()
