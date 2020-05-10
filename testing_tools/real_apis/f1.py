"""
Example uses Ergast Developer API (http://ergast.com/mrd/)
"""

import inflection
import requests

from json_to_models.dynamic_typing import register_datetime_classes
from json_to_models.generator import MetadataGenerator
from json_to_models.models.base import generate_code
from json_to_models.models.pydantic import PydanticModelCodeGenerator
from json_to_models.models.structure import compose_models_flat
from json_to_models.registry import ModelRegistry
from testing_tools.pprint_meta_data import pretty_format_meta
from testing_tools.real_apis import dump_response


def results(season='current', round_code='last'):
    return requests.get(f"http://ergast.com/api/f1/{season}/{round_code}/results.json") \
        .json()['MRData']['RaceTable']['Races']


def drivers(season='current', round_code='last'):
    return requests.get(f"http://ergast.com/api/f1/{season}/{round_code}/drivers.json") \
        .json()['MRData']['DriverTable']['Drivers']


def driver_standings(season='current', round_code='last'):
    return requests.get(f"http://ergast.com/api/f1/{season}/{round_code}/driverStandings.json") \
        .json()['MRData']['StandingsTable']['StandingsLists']


def main():
    results_data = results()
    dump_response("f1", "results", results_data)
    results_data = ("results", results_data)

    drivers_data = drivers()
    dump_response("f1", "drivers", drivers_data)
    drivers_data = ("driver", drivers_data)

    driver_standings_data = driver_standings()
    dump_response("f1", "driver_standings", driver_standings_data)
    driver_standings_data = ("driver_standings", driver_standings_data)

    register_datetime_classes()
    gen = MetadataGenerator()
    reg = ModelRegistry()
    # for name, data in (results_data, drivers_data, driver_standings_data):
    for name, data in (driver_standings_data,):
        fields = gen.generate(*data)
        reg.process_meta_data(fields, model_name=inflection.camelize(name))
    reg.merge_models(generator=gen)
    reg.generate_names()

    for model in reg.models:
        print(pretty_format_meta(model))
        print("=" * 20, end='')

    structure = compose_models_flat(reg.models_map)
    # print('\n', json_format([structure[0], {str(a): str(b) for a, b in structure[1].items()}]))
    # print("=" * 20)

    print(generate_code(structure, PydanticModelCodeGenerator, class_generator_kwargs={}))


if __name__ == '__main__':
    main()
