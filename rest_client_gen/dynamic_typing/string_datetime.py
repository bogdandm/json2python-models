import operator
from datetime import date, datetime, time
from typing import Any, Optional, Type, Union

import dateutil.parser

from .string_serializable import StringSerializable, StringSerializableRegistry, registry

_dt_args_getter = operator.attrgetter('year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond', 'tzinfo')
_d_args_getter = operator.attrgetter('year', 'month', 'day')
_t_args_getter = operator.attrgetter('hour', 'minute', 'second', 'microsecond', 'tzinfo')


def extend_datetime(d: Union[date, time, datetime], cls: Union[Type[date], Type[time], Type[datetime]]) -> Any:
    """
    Wrap datetime object into datetime subclass

    :param d: date/time/datetime instance
    :param cls: datetime subclass
    :return:
    """
    if isinstance(d, datetime):
        args = _dt_args_getter
    elif isinstance(d, time):
        args = _t_args_getter
    else:
        args = _d_args_getter
    return cls(*args(d))


_check_values_date = (
    datetime(2018, 1, 2, 0, 4, 5, 678, tzinfo=None),
    datetime(2018, 1, 2, 9, 4, 5, 678, tzinfo=None)
)


def is_date(s: str) -> Optional[date]:
    """
    Return date instance if given string is a date and None otherwise

    :param s: string
    :return: date or None
    """
    # dateutil.parser.parse replaces missing parts of datetime with values from default value
    # so if there is hour part in given string then d1 and d2 would be equal and string is not pure date
    d1 = dateutil.parser.parse(s, default=_check_values_date[0])
    d2 = dateutil.parser.parse(s, default=_check_values_date[1])
    return None if d1 == d2 else d1.date()


_check_values_time = (
    datetime(2018, 10, 11),
    datetime(2018, 12, 30)
)


def is_time(s: str) -> Optional[time]:
    """
    Return time instance if given string is a time and None otherwise

    :param s: string
    :return: time or None
    """
    d1 = dateutil.parser.parse(s, default=_check_values_time[0])
    d2 = dateutil.parser.parse(s, default=_check_values_time[1])
    return None if d1 == d2 else d1.time()


class IsoDateString(StringSerializable, date):
    """
    Parse date using dateutil.parser.isoparse. Representation format always is ``YYYY-MM-DD``.
    You can override to_representation method to customize it. Just don't forget to call registry.remove(IsoDateString)
    """

    @classmethod
    def to_internal_value(cls, value: str) -> 'IsoDateString':
        if not is_date(value):
            raise ValueError(f"'{value}' is not valid date")
        dt = dateutil.parser.isoparse(value)
        return extend_datetime(dt.date(), cls)

    def to_representation(self):
        return self.isoformat()

    def replace(self, *args, **kwargs) -> 'IsoDateString':
        # noinspection PyTypeChecker
        return date.replace(self, *args, **kwargs)


class IsoTimeString(StringSerializable, time):
    """
    Parse time using dateutil.parser.parse. Representation format always is ``hh:mm:ss.ms``.
    You can override to_representation method to customize it.
    """

    @classmethod
    def to_internal_value(cls, value: str) -> 'IsoTimeString':
        t = is_time(value)
        if not t:
            raise ValueError(f"'{value}' is not valid time")
        return extend_datetime(t, cls)

    def to_representation(self):
        return self.isoformat()

    def replace(self, *args, **kwargs) -> 'IsoTimeString':
        # noinspection PyTypeChecker
        return time.replace(self, *args, **kwargs)


class IsoDatetimeString(StringSerializable, datetime):
    """
    Parse datetime using dateutil.parser.isoparse.
    Representation format always is ``YYYY-MM-DDThh:mm:ss.ms`` (datetime.isoformat method).
    """

    @classmethod
    def to_internal_value(cls, value: str) -> 'IsoDatetimeString':
        dt = dateutil.parser.isoparse(value)
        return extend_datetime(dt, cls)

    def to_representation(self):
        return self.isoformat()

    def replace(self, *args, **kwargs) -> 'IsoDatetimeString':
        # noinspection PyTypeChecker
        return datetime.replace(self, *args, **kwargs)


def register_datetime_classes(registry: StringSerializableRegistry = registry):
    """
    Register datetime classes in given registry (using default registry if no arguments is passed).
    Date parsing is expensive operation so this classes are disabled by default
    """
    registry.add(cls=IsoDateString)
    registry.add(cls=IsoTimeString)
    registry.add(cls=IsoDatetimeString)
