from typing import Dict, List, Set, Tuple

import pytest

from json_to_models.dynamic_typing import ModelMeta
from json_to_models.generator import MetadataGenerator
from json_to_models.models import ListEx, compose_models, extract_root
from json_to_models.registry import ModelRegistry


def test_list_ex():
    l = ListEx(range(10))
    assert l.safe_index('a') is None
    assert l.safe_index(5) == 5
    assert l._safe_indexes(*'abc') == []
    assert l._safe_indexes(*range(20)) == list(range(10))
    l.insert_before('a', 5, 3, 1)
    assert l == [0, 'a', *range(1, 10)]
    l.insert_after('b', 5, 3, 1)
    assert l == [0, 'a', *range(1, 6), 'b', *range(6, 10)]


def indexes_to_names(reg: ModelRegistry, *ix):
    for i in ix:
        yield reg.models_map[i].name


def names_to_indexes(reg: ModelRegistry, *ix):
    for i in ix:
        yield reg.models_map[i].name


# This test relies on model names as a some sort of models ids
# and may fail if some logic of their generation will be changed
# List of Tuple[root_model_name, JSON data] | Dict[model_name, Set[root_model_names]]
test_extract_root_data = [
    pytest.param(
        [
            ("TestModelA", {
                "count": 1,
                "items": [
                    {
                        "x": .5,
                        "y": .1
                    }
                ]
            }),
            ("TestModelB", {
                "next": "some_url",
                "prev": None,
                "count": 2000,
                "items": [
                    {
                        "x": .5,
                        "y": .1
                    }
                ]
            }),
        ],
        {
            'Item': {'TestModelA', 'TestModelB'},
            'TestModelA': set()
        }
    ),
    pytest.param(
        [
            ("TestModelA", {
                "count": 1,
                "items": [
                    {
                        "x": .5,
                        "y": .1
                    }
                ]
            }),
            ("TestModelB", {
                "count": 1,
                "items": [
                    {
                        "x": .5,
                        "y": .1
                    }
                ]
            }),
        ],
        {
            'Item': {'TestModelA_TestModelB'},
            'TestModelA_TestModelB': set()
        },
        id="merge_root"
    )
]


@pytest.mark.parametrize("value,expected", test_extract_root_data)
def test_extract_root(models_generator: MetadataGenerator, models_registry: ModelRegistry,
                      value: List[Tuple[str, dict]], expected: Dict[str, Set[str]]):
    for model_name, data in value:
        fields = models_generator.generate(data)
        models_registry.process_meta_data(fields, model_name=model_name)
    models_registry.merge_models(models_generator)
    models_registry.generate_names()
    names_map = {model.index: model.name for model in models_registry.models}
    names_map.update({model.name: model.index for model in models_registry.models})
    for model_name, roots in expected.items():
        meta = models_registry.models_map[names_map[model_name]]
        extracted_roots = {names_map[ix] for ix in extract_root(meta)}
        assert extracted_roots == roots


base_dict = {"field_" + str(i): int for i in range(20)}

# This test relies on model names as a some sort of models ids
# List of Tuple[root_model_name, model-meta] | List[Tuple[model_name, nested_models]]]
# where nested_models is a recursive definition
test_compose_models_data = [
    pytest.param(
        [
            ("A", {
                "field1": int,
                "item": {
                    "another_field": float
                }
            })
        ],
        [
            ("A", [
                ("Item", [])
            ])
        ],
        {},
        id="basic_test"
    ),
    pytest.param(
        [
            ("RootA", {
                "item": {
                    "field": float
                }
            }),
            ("RootB", {
                "item": {
                    "field": float
                },
                "idontwantrootmodelstomerge": bool
            })
        ],
        [
            ("Item", []),
            ("RootA", []),
            ("RootB", [])
        ],
        {},
        id="global_nested_model"
    ),
    pytest.param(
        [
            ("RootA", {
                "item": {
                    "field": float
                }
            }),
            ("RootB", {
                "item": {
                    "field": float
                }
            })
        ],
        [
            ("RootA_RootB", [
                ("Item", [])
            ])
        ],
        {},
        id="roots_merge"
    ),
    pytest.param(
        [
            ("RootFirst", {
                "root_field": float
            }),
            ("RootA", {
                "item": {
                    "field": float
                }
            }),
            ("RootB", {
                "item": {
                    "field": float
                },
                "idontwantrootmodelstomerge": bool
            })
        ],
        [
            ("RootFirst", []),
            ("Item", []),
            ("RootA", []),
            ("RootB", [])
        ],
        {},
        id="root_order"
    ),
    pytest.param(
        [
            ("Root", {
                "model_a": {
                    "field_a": {
                        "field": float
                    }
                },
                "model_b": {
                    "field_b": {
                        "field": float
                    }
                }
            }),
        ],
        [
            ("Root", [
                ("FieldA_FieldB", []),
                ("ModelA", []),
                ("ModelB", []),
            ])
        ],
        {'FieldA_FieldB': 'Root'},
        id="generic_in_nested_models"
    ),
    pytest.param(
        [
            ("RootItem", {
                "field": float
            }),
            ("RootA", {
                "item": {
                    "field": float
                },
                **base_dict
            }),
            ("RootB", base_dict)
        ],
        [
            ("RootItem", []),
            ("RootA_RootB", [])
        ],
        {},
        id="merge_with_root_model"
    ),
    pytest.param(
        [
            ("Root", {
                "model_a": {
                    "field_a": {
                        "field": {
                            "nested_field": float
                        }
                    }
                },
                "model_b": {
                    "field_b": {
                        "field": {
                            "nested_field": float
                        }
                    }
                }
            }),
        ],
        [
            ("Root", [
                ("FieldA_FieldB", [
                    ("Field", [])
                ]),
                ("ModelA", []),
                ("ModelB", []),
            ])
        ],
        {'FieldA_FieldB': 'Root'},
        id="generic_in_nested_models_with_nested_model"
    ),
]


@pytest.mark.parametrize("value,expected,expected_mapping", test_compose_models_data)
def test_compose_models(
        models_generator: MetadataGenerator, models_registry: ModelRegistry,
        value: List[Tuple[str, dict]], expected: List[Tuple[str, list]], expected_mapping: Dict[str, str]
):
    for model_name, metadata in value:
        models_registry.process_meta_data(metadata, model_name=model_name)
    models_registry.merge_models(models_generator)
    models_registry.generate_names()
    names_map = {model.index: model.name for model in models_registry.models}
    names_map.update({model.name: model.index for model in models_registry.models})
    root, mapping = compose_models(models_registry.models_map)

    def check(nested_value: List[dict], nested_expected: List[Tuple[str, list]]):
        for model_dict, (model_name, nested) in zip(nested_value, nested_expected):
            assert model_dict["model"].name == model_name
            assert len(model_dict["nested"]) == len(nested), f"(Parent model is {model_name})"
            check(model_dict["nested"], nested)

    check(root, expected)

    name = lambda model: model.name if isinstance(model, ModelMeta) else model
    mapping = {name(model): name(parent) for model, parent in mapping.items()}
    assert mapping == expected_mapping
