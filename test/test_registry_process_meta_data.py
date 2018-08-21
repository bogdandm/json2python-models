from collections import OrderedDict

import pytest

from rest_client_gen.dynamic_typing import DOptional, MetaData, SingleType, ComplexType, DTuple
from rest_client_gen.registry import ModelRegistry, ModelMeta, ModelPtr

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
                    ('e', int),
                    ('f', float)
                ]),
                OrderedDict([
                    ('g', int),
                    ('h', float)
                ]),
            ))
        ]),
        [
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
                        ('e', int),
                        ('f', float)
                    ]),
                    OrderedDict([
                        ('g', int),
                        ('h', float)
                    ]),
                ))
            ]),
            OrderedDict([
                ('a', int),
                ('b', float)
            ]),
            OrderedDict([
                ('c', int),
                ('d', float)
            ]),
            OrderedDict([
                ('e', int),
                ('f', float)
            ]),
            OrderedDict([
                ('g', int),
                ('h', float)
            ]),
        ],
        id="complex"
    ),
]


def check_type(meta: MetaData, expected: MetaData):
    if isinstance(meta, dict):
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
