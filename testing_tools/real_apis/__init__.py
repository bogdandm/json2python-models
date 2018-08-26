import json
from pathlib import Path

BASE_PATH = (Path(__file__) / '..').resolve().absolute()


def dump_response(app, name, data):
    folder = BASE_PATH / app
    folder.mkdir(exist_ok=True)
    with (folder / f"{name}.json").open("w") as f:
        json.dump(data, f, indent=4)
