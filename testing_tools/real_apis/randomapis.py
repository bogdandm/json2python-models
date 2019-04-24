"""
Example uses the following APIs:
- CHRONICLING API (https://chroniclingamerica.loc.gov/about/api/)
- Launch Library Reading API (https://launchlibrary.net/docs/1.3/api.html)
- University Domains and Names Data List (https://github.com/Hipo/university-domains-list)
"""
import requests

from json_to_models.generator import MetadataGenerator
from json_to_models.models.attr import AttrsModelCodeGenerator
from json_to_models.models.base import generate_code
from json_to_models.models.structure import compose_models
from json_to_models.registry import ModelRegistry
from testing_tools.real_apis import dump_response


def chroniclingamerica(tag="michigan"):
    return requests.get(f"http://chroniclingamerica.loc.gov/search/titles/results/?terms={tag}&format=json").json()


def launchlibrary(mission_name="GPS"):
    return requests.get(f"https://launchlibrary.net/1.3/mission/{mission_name}").json()


def university_domains():
    return requests.get("https://raw.githubusercontent.com/Hipo/university-domains-list/master/"
                        "world_universities_and_domains.json").json()


def main():
    chroniclingamerica_data = chroniclingamerica()
    dump_response("other", "chroniclingamerica", chroniclingamerica_data)

    launchlibrary_data = launchlibrary()
    dump_response("other", "launchlibrary", launchlibrary_data)

    university_domains_data = university_domains()
    dump_response("other", "university_domains", university_domains_data)

    gen = MetadataGenerator()
    reg = ModelRegistry()
    for data in ([chroniclingamerica_data], [launchlibrary_data], university_domains_data):
        fields = gen.generate(*data)
        reg.process_meta_data(fields)
    reg.merge_models(generator=gen)
    reg.generate_names()
    structure = compose_models(reg.models_map)
    print(generate_code(structure, AttrsModelCodeGenerator))


if __name__ == '__main__':
    main()
