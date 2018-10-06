from typing import Iterable

import pytest

from json_to_models.dynamic_typing import DList, DOptional, ModelMeta, Unknown
from json_to_models.generator import MetadataGenerator
from json_to_models.registry import ModelRegistry
from test.test_registry.test_registry_process_meta_data import check_type, cycle_ref, test_data as base_test_data

# Include test cases from `test_registry_process_meta_data.py`. They should be correct.
# At least until their not contains any models with same keys.
# Original MetaData | Merged models
test_data = base_test_data + [
    pytest.param(
        [
            {
                'a': int,
                'b': float
            },
            {
                'a': int,
                'b': float
            }
        ],
        [
            {
                'a': int,
                'b': float
            }
        ],
        id="simple_merge"
    ),
    pytest.param(
        [
            {
                'd': int,
                'e': float
            },
            {
                'a': int,
                'b': float
            },
            {
                'a': int,
                'b': float
            }
        ],
        [
            {
                'd': int,
                'e': float
            },
            {
                'a': int,
                'b': float
            }
        ],
        id="simple_merge_with_other_model"
        # Also test sort_models by this test case
    ),
    pytest.param(
        [
            {
                'a': int,
                'b': float
            },
            {
                'd': int,
                'e': {
                    'a': int,
                    'b': float
                },
            }
        ],
        [
            {
                'a': int,
                'b': float
            },
            {
                'd': int,
                'e': {
                    'a': int,
                    'b': float
                },
            }
        ],
        id="merge_nested"
    ),
    pytest.param(
        {
            'int': int,
            'items': DList({
                'int': int,
                'items': DList(Unknown)  # Empty list
            })
        },
        [
            {
                'int': int,
                'items': DList({
                    'int': int,
                    'items': DList(cycle_ref)
                })
            }
        ],
        id="cycle"
    ),
    pytest.param(
        {
            'int': int,
            'items': {
                'count': int,
                'wrapper': DList({
                    'int': int,
                    'items': Unknown  # null
                })
            }
        },
        [
            {
                'int': int,
                'items': {
                    'count': int,
                    'wrapper': DList({
                        'int': int,
                        'items': {
                            'count': int,
                            'wrapper': DList(cycle_ref)
                        }
                    })
                }
            },
            {
                'count': int,
                'wrapper': DList({
                    'int': int,
                    'items': {
                        'count': int,
                        'wrapper': DList(cycle_ref)
                    }
                })
            }
        ],
        id="cycle_with_wrapper"
    ),
    pytest.param(
        [
            {
                "field" + str(i): int for i in range(10)
            },
            {
                "field" + str(i): int for i in range(1, 10)
            },
            {
                "field" + str(i): int for i in range(9)
            }
        ],
        [
            {
                "field0": DOptional(int),
                **{
                    "field" + str(i): int for i in range(1, 9)
                },
                "field9": DOptional(int),
            }
        ],
        id="merge_models"
    ),
    pytest.param(
        [
            {
                "field" + str(i): int for i in range(10)
            },
            {
                "field" + str(i): int for i in range(5, 10)
            },
            {
                "field" + str(i): int for i in range(5)
            }
        ],
        [
            {
                "field" + str(i): int for i in range(10)
            },
            {
                "field" + str(i): int for i in range(5, 10)
            },
            {
                "field" + str(i): int for i in range(5)
            }
        ],
        id="not_merge_models"
    ),
    pytest.param(
        [
            {
                "field" + str(i): int for i in range(10)
            },
            {
                "field" + str(i): (int if i < 9 else DOptional(int)) for i in range(10)
            },
            {
                "field" + str(i): int for i in range(9)
            }
        ],
        [
            {
                **{
                    "field" + str(i): int for i in range(9)
                },
                "field9": DOptional(int),
            }
        ],
        id="merge_models_with_optional_field"
    ),
]


def sort_models(models: Iterable[ModelMeta]):
    return sorted(
        models,
        key=lambda model: ",".join(sorted(
            (model if isinstance(model, dict) else model.type).keys()
        ))
    )


@pytest.mark.parametrize("value,expected", test_data)
def test_registry_merge_models_base(models_generator: MetadataGenerator, models_registry: ModelRegistry, value,
                                    expected):
    if isinstance(value, list):
        for v in value:
            models_registry.process_meta_data(v)
    else:
        models_registry.process_meta_data(value)
    models_registry.merge_models(generator=models_generator)
    assert len(models_registry.models) == len(expected)
    for model, expected_model in zip(sort_models(models_registry.models), sort_models(expected)):
        check_type(model, expected_model)
