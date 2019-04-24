import datetime

import pytest

from json_to_models.dynamic_typing import (BooleanString, FloatString, IntString, IsoDateString, IsoDatetimeString,
                                           IsoTimeString, register_datetime_classes)
from json_to_models.generator import MetadataGenerator

register_datetime_classes()

test_detect_type_data = [
    # Check that string datetime doesn't break default string types
    pytest.param(
        "1",
        IntString,
        id="default_check_int"
    ),
    pytest.param(
        "1.5",
        FloatString,
        id="default_check_float"
    ),
    pytest.param(
        "true",
        BooleanString,
        id="bool"
    ),
    pytest.param(
        "2018-12-31",
        IsoDateString,
        id="date"
    ),
    pytest.param(
        "12:58",
        IsoTimeString,
        id="time"
    ),
    pytest.param(
        "2018-12-31T12:58:12Z",
        IsoDatetimeString,
        id="datetime"
    )
]


@pytest.mark.parametrize("value,expected", test_detect_type_data)
def test_detect_type(models_generator: MetadataGenerator, value, expected):
    result = models_generator._detect_type(value)
    assert result == expected


test_parse_data = [
    pytest.param(
        "true",
        BooleanString(True),
        id="bool"
    ),
    pytest.param(
        "2018-12-31",
        IsoDateString(2018, 12, 31),
        id="date"
    ),
    pytest.param(
        "12:13",
        IsoTimeString(12, 13),
        id="time"
    ),
    pytest.param(
        "04:15:34",
        IsoTimeString(4, 15, 34),
        id="time_seconds"
    ),
    pytest.param(
        "04:15:34.034",
        IsoTimeString(4, 15, 34, 34000),
        id="time_ms"
    ),
    pytest.param(
        "2018-12-04T04:15:34.034000+00:00",
        IsoDatetimeString(2018, 12, 4, 4, 15, 34, 34000, tzinfo=datetime.timezone.utc),
        id="datetime_full"
    ),
    pytest.param(
        "2018-12-04T04:15",
        IsoDatetimeString(2018, 12, 4, 4, 15),
        id="datetime_partial"
    )
]


@pytest.mark.parametrize("value,expected", test_parse_data)
def test_parse(models_generator: MetadataGenerator, value, expected):
    cls = models_generator._detect_type(value)
    result = cls.to_internal_value(value)
    assert result == expected
    assert value in result.to_representation()


def test_replace():
    assert IsoTimeString(14, 12, 57).replace(minute=58, second=32) == IsoTimeString(14, 58, 32)
    assert IsoDateString(2014, 12, 5).replace(day=4, month=5) == IsoDateString(2014, 5, 4)
    assert IsoDatetimeString(2014, 12, 5, 14, 12, 57).replace(minute=58, second=32, day=4, month=5) \
           == IsoDatetimeString(2014, 5, 4, 14, 58, 32)
