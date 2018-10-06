from collections import OrderedDict

import pytest

from json_to_models.dynamic_typing import ComplexType, DOptional, DTuple, MetaData, ModelMeta, ModelPtr, SingleType
from json_to_models.registry import ModelRegistry

# MetaData | List of models
test_data = [
    pytest.param(
        OrderedDict([
            ('a', int),
            ('b', float)
        ]),
        [
            OrderedDict([
                ('a', int),
                ('b', float)
            ])
        ],
        id="flat"
    ),
    pytest.param(
        OrderedDict([
            ('nested', OrderedDict([
                ('a', int),
                ('b', float)
            ])),
            ('b', float)
        ]),
        [
            OrderedDict([
                ('nested', OrderedDict([
                    ('a', int),
                    ('b', float)
                ])),
                ('b', float)
            ]),
            OrderedDict([
                ('a', int),
                ('b', float)
            ])
        ],
        id="nested"
    ),
    pytest.param(
        OrderedDict([
            ('nested', OrderedDict([
                ('a', int),
                ('b', float)
            ])),
            ('nested_single', DOptional(OrderedDict([
                ('c', int),
                ('d', float)
            ]))),
            ('nested_complex', DTuple(
                OrderedDict([
                    ('nested_2', DOptional(OrderedDict([
                        ('x', int),
                        ('y', float)
                    ]))),
                    ('f', float)
                ]),
                OrderedDict([
                    ('g', int),
                    ('h', float)
                ]),
            ))
        ]),
        [
            # 1A
            OrderedDict([
                ('nested', OrderedDict([
                    ('a', int),
                    ('b', float)
                ])),
                ('nested_single', DOptional(OrderedDict([
                    ('c', int),
                    ('d', float)
                ]))),
                ('nested_complex', DTuple(
                    OrderedDict([
                        ('nested_2', DOptional(OrderedDict([
                            ('x', int),
                            ('y', float)
                        ]))),
                        ('f', float)
                    ]),
                    OrderedDict([
                        ('g', int),
                        ('h', float)
                    ]),
                ))
            ]),
            # 1B
            OrderedDict([
                ('a', int),
                ('b', float)
            ]),
            # 1C
            OrderedDict([
                ('c', int),
                ('d', float)
            ]),
            # 1D
            OrderedDict([
                ('nested_2', DOptional(OrderedDict([
                    ('x', int),
                    ('y', float)
                ]))),
                ('f', float)
            ]),
            # 1E
            OrderedDict([
                ('x', int),
                ('y', float)
            ]),
            # 1F
            OrderedDict([
                ('g', int),
                ('h', float)
            ]),
        ],
        id="complex"
    ),
]

# use it as value in expected model dict to mark this field as cycle reference
cycle_ref = object()


def check_type(meta: MetaData, expected: MetaData):
    if expected is cycle_ref:
        assert isinstance(meta, ModelMeta) or isinstance(meta, ModelPtr)

    elif isinstance(meta, dict):
        assert isinstance(expected, dict)
        for k, v in meta.items():
            check_type(v, expected[k])

    elif isinstance(meta, ModelMeta) or isinstance(meta, ModelPtr):
        check_type(meta.type, expected)

    elif isinstance(meta, SingleType):
        assert isinstance(expected, type(meta))
        check_type(meta.type, expected.type)

    elif isinstance(meta, ComplexType):
        assert isinstance(expected, type(meta))
        for t1, t2 in zip(meta, expected):
            check_type(t1, t2)

    else:
        assert meta == expected


@pytest.mark.parametrize("value,expected", test_data)
def test_registry_process_meta_data(models_registry: ModelRegistry, value, expected):
    models_registry.process_meta_data(value)
    assert len(models_registry.models) == len(expected)
    for model, expected_model in zip(models_registry.models, expected):
        check_type(model, expected_model)


expected_pointers = OrderedDict([
    ("1A", None),
    ("1B", "1A"),
    ("1C", "1A"),
    ("1D", "1A"),
    ("1E", "1D"),
    ("1F", "1A")
])


@pytest.mark.parametrize("value,expected", (pytest.param(
    test_data[2].values[0],
    expected_pointers,
    id="base_test"
),))
def test_registry_pointers(models_registry: ModelRegistry, value, expected):
    models_registry.process_meta_data(value)
    assert len(models_registry.models) == len(expected)
    for model, (index, parent) in zip(models_registry.models, expected.items()):
        assert model.index == index
        ptr = next(iter(model.pointers))
        assert ptr.parent.index if ptr.parent else None == parent
