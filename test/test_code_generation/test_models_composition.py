from typing import Dict, List, Set, Tuple

import pytest

from json_to_models.dynamic_typing import ModelMeta
from json_to_models.generator import MetadataGenerator
from json_to_models.models.structure import compose_models, compose_models_flat, extract_root
from json_to_models.models.utils import ListEx
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


def _test_compose_models(
        function, request,
        models_generator: MetadataGenerator, models_registry: ModelRegistry,
        value: List[Tuple[str, dict]], expected: List[Tuple[str, list]], expected_mapping: Dict[str, str]
):
    for model_name, metadata in value:
        models_registry.process_meta_data(metadata, model_name=model_name)
    models_registry.merge_models(models_generator)
    models_registry.generate_names()
    names_map = {model.index: model.name for model in models_registry.models}
    names_map.update({model.name: model.index for model in models_registry.models})
    root, mapping = function(models_registry.models_map)

    def check(nested_value: List[dict], nested_expected: List[Tuple[str, list]]):
        for model_dict, (model_name, nested) in zip(nested_value, nested_expected):
            assert model_dict["model"].name == model_name, str(nested_value)
            assert len(model_dict["nested"]) == len(nested), f"(Parent model is {model_name})"
            check(model_dict["nested"], nested)

    check(root, expected)

    name = lambda model: model.name if isinstance(model, ModelMeta) else model
    mapping = {name(model): name(parent) for model, parent in mapping.items()}
    assert mapping == expected_mapping


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
        request,
        models_generator: MetadataGenerator, models_registry: ModelRegistry,
        value: List[Tuple[str, dict]], expected: List[Tuple[str, list]], expected_mapping: Dict[str, str]
):
    _test_compose_models(compose_models, request, models_generator, models_registry, value, expected, expected_mapping)


test_compose_models_flat_data = [
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
            ("A", []),
            ("Item", [])
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
            ("RootA", []),
            ("RootB", []),
            ("Item", []),
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
            ("RootA_RootB", []),
            ("Item", [])
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
            ("RootA", []),
            ("RootB", []),
            ("Item", []),
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
            ("Root", []),
            ("ModelA", []),
            ("ModelB", []),
            ("FieldA_FieldB", []),

        ],
        {},
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
            ("RootA_RootB", []),
            ("RootItem", []),
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
            ("Root", []),
            ("ModelA", []),
            ("ModelB", []),
            ("FieldA_FieldB", []),
            ("Field", [])
        ],
        {},
        id="generic_in_nested_models_with_nested_model"
    ),
    pytest.param(
        [
            ("RootA", {
                "field_a1": {"nested": {"field": int}},
                "field_a2": {"nested_2": {"field_2": int}},
                "nested": {"field": int}
            }),
            ("RootB", {
                "field_b1": {"nested": {"field": int}},
                "field_b2": {"nested_2": {"field_2": int}},
                "nested": {"field": int}
            }),
            ("RootC", {
                "field_c1": float
            }),
        ],
        [
            ("RootA", []),
            ("RootB", []),
            ("RootC", []),
            ("FieldA1_FieldB1", []),
            ("Nested", []),
            ("FieldA2_FieldB2", []),
            ("Nested2", []),
        ],
        {},
        id="sort_1"
    ),
    pytest.param(
        [
            ("RootA", {
                "field_a1": {"field_a1_n": {"field": int}},
                "field_a2": {"field_a2_n": {"field": int}},
                "field_a3": {"field_a3_n": {"field": int}},
                "field_a4": {"field_a4_n": {"field": int}},
            }),
            ("RootB", {
                "field_b1": {"field_b1_n": {"field": int}},
                "field_b2": {"field_b2_n": {"field": int}},
                "field_b3": {"field_b3_n": {"field": int}},
                "field_b4": {"field_b4_n": {"field": int}},
            }),
            ("RootC", {
                "field_c1": {"field_c1_n": {"field": int}},
                "field_c2": {"field_c2_n": {"field": int}},
                "field_c3": {"field_c3_n": {"field": int}},
                "field_c4": {"field_c4_n": {"field": int}},
            }),
        ],
        [
            ("RootA", []),
            ("RootB", []),
            ("RootC", []),
            ("FieldA1", []),
            ("FieldA2", []),
            ("FieldA3", []),
            ("FieldA4", []),
            ("FieldB1", []),
            ("FieldB2", []),
            ("FieldB3", []),
            ("FieldB4", []),
            ("FieldC1", []),
            ("FieldC2", []),
            ("FieldC3", []),
            ("FieldC4", []),
            ("FieldA1N_FieldA2N_FieldA3N_FieldA4N_"
             "FieldB1N_FieldB2N_FieldB3N_FieldB4N_"
             "FieldC1N_FieldC2N_FieldC3N_FieldC4N", []),
        ],
        {},
        id="sort_2"
    ),
    pytest.param(
        [
            ("RootA", {
                "field_a1": {
                    "field_a1_n": {"field_1": int},
                    "field_a1_n2": {"field_11": int},
                },
                "field_a2": {"field_a2_n": {"field_2": int}},
                "field_a3": {"field_a3_n": {"field_3": int}},
                "field_a4": {"field_a4_n": {"field_4": int}},
            }),
            ("RootB", {
                "field_b1": {
                    "field_b1_n": {"field_01": int},
                    "field_b1_n2": {"field_b11": int},
                    "field_b1_n3": {"field_b21": int},
                },
                "field_b2": {"field_b2_n": {"field_02": int}},
                "field_b3": {
                    "field_b3_n": {"field_03": int},
                    "field_b3_n2": {"field_b13": int},
                    "field_b3_n3": {"field_b23": int},
                    "field_b3_n4": {"field_b33": int},
                },
                "field_b4": {"field_b4_n": {"field_04": int}},
            }),
        ],
        [
            ("RootA", []),
            ("RootB", []),

            ("FieldA1", []),
            ("FieldA1N", []),
            ("FieldA1N2", []),

            ("FieldA2", []),
            ("FieldA2N", []),

            ("FieldA3", []),
            ("FieldA3N", []),

            ("FieldA4", []),
            ("FieldA4N", []),

            ("FieldB1", []),
            ("FieldB1N", []),
            ("FieldB1N2", []),
            ("FieldB1N3", []),

            ("FieldB2", []),
            ("FieldB2N", []),

            ("FieldB3", []),
            ("FieldB3N", []),
            ("FieldB3N2", []),
            ("FieldB3N3", []),
            ("FieldB3N4", []),

            ("FieldB4", []),
            ("FieldB4N", []),
        ],
        {},
        id="sort_3"
    ),
]


@pytest.mark.parametrize("value,expected,expected_mapping", test_compose_models_flat_data)
def test_compose_models_flat(
        request,
        models_generator: MetadataGenerator, models_registry: ModelRegistry,
        value: List[Tuple[str, dict]], expected: List[Tuple[str, list]], expected_mapping: Dict[str, str]
):
    _test_compose_models(compose_models_flat, request, models_generator, models_registry, value, expected,
                         expected_mapping)
