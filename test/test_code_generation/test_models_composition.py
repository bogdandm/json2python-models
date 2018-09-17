from typing import Dict, List, Set, Tuple

import pytest

from rest_client_gen.generator import MetadataGenerator
from rest_client_gen.models import ListEx, extract_root
from rest_client_gen.registry import ModelRegistry


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
