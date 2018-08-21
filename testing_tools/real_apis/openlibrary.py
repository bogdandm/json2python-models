import json
from pathlib import Path

import requests

from rest_client_gen.generator import Generator
from rest_client_gen.registry import ModelRegistry
from testing_tools.pprint_meta_data import pprint_gen


def search(s: str) -> dict:
    return requests.get("http://openlibrary.org/search.json", {
        'q': s
    }).json()


if __name__ == '__main__':
    folder = Path("openlibrary")
    folder.mkdir(exist_ok=True)

    SYMBOL = "The Lord of the Rings"

    data = search(SYMBOL)['docs']
    with (folder / "search.json").open("w") as f:
        json.dump(data, f, indent=4)
    print("Start generation")
    gen = Generator()
    reg = ModelRegistry()
    fields = gen.generate(*data)

    for s in pprint_gen(fields):
        print(s, end='')
    print('\n' + '-' * 10, end='')

    for s in pprint_gen(reg.register(fields)):
        print(s, end='')
    print('\n' + '-' * 10, end='')

