import imp
import json
import sys
from inspect import isclass

import pydantic
import pytest

from json_to_models.generator import MetadataGenerator
from json_to_models.models.base import generate_code
from json_to_models.models.pydantic import PydanticModelCodeGenerator
from json_to_models.models.structure import compose_models_flat
from json_to_models.registry import ModelRegistry
from .test_script import test_data_path

test_self_validate_pydantic_data = [
    pytest.param(test_data_path / "gists.json", list, id="gists.json"),
    pytest.param(test_data_path / "users.json", list, id="users.json"),
    pytest.param(test_data_path / "unicode.json", dict, id="unicode.json"),
    pytest.param(test_data_path / "photos.json", dict, id="photos.json"),
]


@pytest.mark.parametrize("data,data_type", test_self_validate_pydantic_data)
def test_self_validate_pydantic(data, data_type):
    with data.open() as f:
        data = json.load(f)

    gen = MetadataGenerator(
        dict_keys_fields=['files']
    )
    reg = ModelRegistry()
    if data_type is not list:
        data = [data]
    fields = gen.generate(*data)
    reg.process_meta_data(fields, model_name="TestModel")
    reg.merge_models(generator=gen)
    reg.generate_names()

    structure = compose_models_flat(reg.models_map)
    code = generate_code(structure, PydanticModelCodeGenerator)
    module = imp.new_module("test_models")
    sys.modules["test_models"] = module
    try:
        exec(compile(code, "test_models.py", "exec"), module.__dict__)
    except Exception as e:
        assert not e, code

    import test_models
    for name in dir(test_models):
        cls = getattr(test_models, name)
        if isclass(cls) and issubclass(cls, pydantic.BaseModel):
            cls.update_forward_refs()
    for item in data:
        obj = test_models.TestModel.parse_obj(item)
        assert obj
