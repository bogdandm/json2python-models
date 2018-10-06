from typing import Set, Tuple

import pytest

from json_to_models.generator import MetadataGenerator
from json_to_models.registry import ModelRegistry

# Tuple[Root model name, JSON data] | Set[Tuple[model_name, is_generated]]
test_data = [
    pytest.param(
        ("test_response", {
            "point_south": {
                "x": 0.4,
                "y": 0.2
            },
            "point_north": {
                "x": 0.4,
                "y": 0.2
            },
            "point_west": {
                "x": 0.4,
                "y": 0.2
            },
            "point_east": {
                "x": 0.4,
                "y": 0.2
            }
        }),
        {("TestResponse", False), ("PointEast_PointNorth_PointSouth_PointWest", True)},
        id="merge_models"
    ),
    pytest.param(
        ("results", {
            "points": [
                {
                    "x": 0.4,
                    "y": 0.2
                },
                {
                    "x": 0.4,
                    "y": 0.2
                },
                {
                    "x": 0.4,
                    "y": 0.2
                },
                {
                    "x": 0.4,
                    "y": 0.2
                }
            ],
            "other_points": [
                {
                    "x": 0.4,
                    "y": 0.2
                },
                {
                    "x": 0.4,
                    "y": 0.2
                },
                {
                    "x": 0.4,
                    "y": 0.2
                },
                {
                    "x": 0.4,
                    "y": 0.2
                }
            ]
        }),
        {("Result", False), ("Point", True)},
        id="extract_generic_name"
    ),
    pytest.param(
        (b"Response", {
            "point_south": {
                "x": 0.4,
                "y": 0.2
            }
        }),
        {("Response", False), ("PointSouth", True)},
        id="raw_name_set"
    ),
    pytest.param(
        ("Point", {
            "x": 0.4,
            "y": 0.2,
            "sub": [{
                "x": 0.3,
                "y": 0.7,
                "sub": []
            }]
        }),
        {("Point", False)},
        id="merge_with_name"
    ),
    pytest.param(
        ("Response", {
            "cats": {
                "a": "asdasd"
            },
            "cat": {
                "b": "dfgertdfgdfg"
            }
        }),
        {("Response", False), ("Cat", True), ("Cat_1C", True)},
        id="duplicates"
    ),
]


@pytest.mark.parametrize("value,expected", test_data)
def test_models_names(models_generator: MetadataGenerator, models_registry: ModelRegistry,
                      value: Tuple[str, dict], expected: Set[Tuple[str, bool]]):
    model_name, data = value
    fields = models_generator.generate(data)
    if isinstance(model_name, bytes):
        models_registry.process_meta_data(fields, model_name=model_name.decode())
    elif isinstance(model_name, str):
        ptr = models_registry.process_meta_data(fields)
        ptr.type.name = model_name
    models_registry.merge_models(models_generator)
    models_registry.generate_names()
    names = {(model.name, model.is_name_generated) for model in models_registry.models}
    assert names == expected
