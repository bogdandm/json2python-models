import json
from datetime import datetime
from pathlib import Path

from json_to_models.generator import MetadataGenerator
from json_to_models.models import compose_models
from json_to_models.models.attr import AttrsModelCodeGenerator
from json_to_models.models.base import generate_code
from json_to_models.registry import ModelRegistry


def load_data() -> dict:
    with (Path(__file__) / ".." / ".." / "large_data_set.json").open() as f:
        data = json.load(f)
    return data


def main():
    data = load_data()

    start_t = datetime.now()
    gen = MetadataGenerator(
        dict_keys_regex=[r"^\d+(?:\.\d+)?$", r"^(?:[\w ]+/)+[\w ]+\.[\w ]+$"],
        dict_keys_fields=["assets"]
    )
    reg = ModelRegistry()
    fields = gen.generate(data)
    reg.process_meta_data(fields, model_name="SkillTree")
    reg.merge_models(generator=gen)
    reg.generate_names()

    structure = compose_models(reg.models_map)
    code = generate_code(structure, AttrsModelCodeGenerator, class_generator_kwargs={"no_meta": True})
    print(code)
    # with open("tmp.py", "w") as f:
    #     f.write(code)
    print(f"{(datetime.now() - start_t).total_seconds():.4f} seconds")


if __name__ == '__main__':
    main()
