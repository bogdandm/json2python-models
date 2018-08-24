import requests

from rest_client_gen.generator import Generator
from rest_client_gen.registry import ModelRegistry
from testing_tools.pprint_meta_data import pprint_gen
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

    gen = Generator()
    reg = ModelRegistry()
    for data in ([chroniclingamerica_data], [launchlibrary_data]):
        fields = gen.generate(*data)

        for s in pprint_gen(fields):
            print(s, end='')
        print('\n' + '-' * 10, end='')

        model = reg.process_meta_data(fields)
        for s in pprint_gen(model):
            print(s, end='')
        print('\n' + '-' * 10, end='')


if __name__ == '__main__':
    main()
