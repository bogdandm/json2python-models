"""
City Lots San Francisco dataset (https://github.com/zemirco/sf-city-lots-json)
"""
import json
from datetime import datetime

try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x, **kwargs: x
from json_to_models.generator import MetadataGenerator
from json_to_models.models.structure import compose_models
from json_to_models.models.attr import AttrsModelCodeGenerator
from json_to_models.models.base import generate_code
from json_to_models.registry import ModelRegistry
import requests

URL = "https://raw.githubusercontent.com/zemirco/sf-city-lots-json/master/citylots.json"


def load_data() -> dict:
    r = requests.get(URL, stream=True)
    total_size = int(r.headers.get('content-length', 0))
    block_size = 1024 * 1024
    bytes_data = b""
    print(f"Start downloading data (total size {total_size / block_size:.2f}Mb)")
    for data in tqdm(r.iter_content(block_size), total=total_size // block_size, unit='Mb', unit_scale=True):
        bytes_data += data
    data = bytes_data.decode("utf-8")
    return json.loads(data)


def main():
    data = load_data()

    start_t = datetime.now()
    gen = MetadataGenerator()
    reg = ModelRegistry()
    print("Start generating metadata...")
    fields = gen.generate(data)
    print("Start generating models tree...")
    reg.process_meta_data(fields, model_name="Cities")
    print("Merging models...")
    reg.merge_models(generator=gen)
    print("Generating names...")
    reg.generate_names()

    print("Generating structure...")
    structure = compose_models(reg.models_map)
    print("Generating final code...")
    code = generate_code(structure, AttrsModelCodeGenerator)
    print(code)
    print(f"{(datetime.now() - start_t).total_seconds():.4f} seconds")


if __name__ == '__main__':
    main()
