"""
Example uses Ergast Developer API (http://ergast.com/mrd/)
"""
import inflection
import requests

from rest_client_gen.generator import Generator
from rest_client_gen.registry import ModelRegistry
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
    drivers_data = ("drivers", drivers_data)

    driver_standings_data = driver_standings()
    dump_response("f1", "driver_standings", driver_standings_data)
    driver_standings_data = ("driver_standings", driver_standings_data)

    gen = Generator()
    reg = ModelRegistry()
    for name, data in (results_data, drivers_data, driver_standings_data):
        fields = gen.generate(*data)
        model_ptr = reg.process_meta_data(fields)
        model_ptr.type.set_raw_name(inflection.camelize(name))
    reg.merge_models(generator=gen)
    for model in reg.models:
        model.generate_name()

    for model in reg.models:
        print(pretty_format_meta(model))
        print("=" * 20, end='')


if __name__ == '__main__':
    main()
