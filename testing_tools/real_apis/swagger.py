import json
from pathlib import Path

from json_to_models.dynamic_typing.string_serializable import StringSerializable, registry
from json_to_models.generator import MetadataGenerator
from json_to_models.models.attr import AttrsModelCodeGenerator
from json_to_models.models.base import generate_code
from json_to_models.models.structure import compose_models_flat
from json_to_models.registry import ModelFieldsNumberMatch, ModelFieldsPercentMatch, ModelRegistry


@registry.add()
class SwaggerRef(StringSerializable, str):
    @classmethod
    def to_internal_value(cls, value: str) -> 'SwaggerRef':
        if not value.startswith("#/"):
            raise ValueError(f"invalid literal for SwaggerRef: '{value}'")
        return cls(value)

    def to_representation(self) -> str:
        return str(self)


def load_data() -> dict:
    with (Path(__file__) / ".." / ".." / "swagger.json").resolve().open() as f:
        data = json.load(f)
    return data


def main():
    data = load_data()

    gen = MetadataGenerator(
        dict_keys_regex=[],
        dict_keys_fields=["securityDefinitions", "paths", "responses", "definitions", "properties"]
    )
    reg = ModelRegistry(ModelFieldsPercentMatch(.5), ModelFieldsNumberMatch(10))
    fields = gen.generate(data)
    reg.process_meta_data(fields, model_name="Swagger")
    reg.merge_models(generator=gen)
    reg.generate_names()

    structure = compose_models_flat(reg.models_map)
    code = generate_code(structure, AttrsModelCodeGenerator)
    print(code)


if __name__ == '__main__':
    main()
