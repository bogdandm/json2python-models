import json
from datetime import datetime
from pathlib import Path

from json_to_models.generator import MetadataGenerator
from json_to_models.models.attr import AttrsModelCodeGenerator
from json_to_models.models.base import generate_code
from json_to_models.models.dataclasses import DataclassModelCodeGenerator
from json_to_models.models.structure import compose_models, compose_models_flat
from json_to_models.registry import ModelRegistry


def load_data() -> dict:
    with (Path(__file__) / ".." / ".." / "large_data_set.json").resolve().open() as f:
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
    code = generate_code(structure, AttrsModelCodeGenerator)
    print(code)

    print("=" * 10, f"{(datetime.now() - start_t).total_seconds():.4f} seconds", "=" * 10,
          "\nPress enter to continue...\n")
    input()
    structure_flat = compose_models_flat(reg.models_map)
    code = generate_code(structure_flat, DataclassModelCodeGenerator, class_generator_kwargs={"meta": True})
    print(code)


if __name__ == '__main__':
    main()
