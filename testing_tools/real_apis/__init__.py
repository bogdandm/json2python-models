import json
from pathlib import Path


def dump_response(app, name, data):
    # TODO: Make Path absolute
    folder = Path(app)
    folder.mkdir(exist_ok=True)
    with (folder / f"{name}.json").open("w") as f:
        json.dump(data, f, indent=4)