import sys
from pathlib import Path

import pytest

from json_to_models.cli import _process_path, dict_lookup, iter_json_file, path_split, safe_json_load
from json_to_models.utils import convert_args

echo = lambda *args, **kwargs: (args, kwargs)
test_dict = {"user":
    {
        "id": 1,
        "name": "Leanne Graham",
        "username": "Bret",
        "email": "Sincere@april.biz",
        "address": {
            "street": "Kulas Light",
            "suite": "Apt. 556",
            "city": "Gwenborough",
            "zipcode": "92998-3874",
            "geo": {
                "lat": "-37.3159",
                "lng": "81.1496"
            }
        },
        "phone": "1-770-736-8031 x56442",
        "website": "hildegard.org",
        "company": {
            "name": "Romaguera-Crona",
            "catchPhrase": "Multi-layered client-server neural-net",
            "bs": "harness real-time e-markets"
        }
    }
}
path = (Path(__file__) / "..").resolve()

# Data structure: function | (arguments, kwargs) | expected (args, kwargs)
test_convert_args_data = [
    pytest.param(
        convert_args(echo, int, float),
        (("10", "15.5"), {}),
        ((10, 15.5), {}),
        id="base"
    ),
    pytest.param(
        convert_args(echo, int, float),
        (("10", "15.5", "abc", "qwerty"), {}),
        ((10, 15.5, "abc", "qwerty"), {}),
        id="extra_args"
    ),
    pytest.param(
        convert_args(echo, int, float, x=int, y=float),
        (("10", "15.5", "abc", "qwerty"), {'x': '0', 'y': '1.5', 'z': '0'}),
        ((10, 15.5, "abc", "qwerty"), {'x': 0, 'y': 1.5, 'z': '0'}),
        id="kwargs"
    )
]


@pytest.mark.parametrize("fn,value,expected", test_convert_args_data)
def test_convert_args(fn, value, expected):
    args, kwargs = value
    result = fn(*args, **kwargs)
    assert result == expected, f"(in value: {value})"


test_path_split_data = [
    pytest.param("./test/file.txt", ['.', 'test', 'file.txt'], id='base'),
    pytest.param("/tmp/test/file.txt", ['/', 'tmp', 'test', 'file.txt'], id='unix path'),
    pytest.param("test/*.txt", ['test', '*.txt'], id='pattern'),
    pytest.param("test/**/*.txt", ['test', '**', '*.txt'], id='recursive pattern'),
]

if sys.platform.startswith("win"):
    test_path_split_data.append(pytest.param("X:/test/file.txt", ['X:/', 'test', 'file.txt'], id='windows path'))
else:
    test_path_split_data.append(pytest.param("X:/test/file.txt", ['X:', 'test', 'file.txt'], id='windows path'))


@pytest.mark.parametrize("value,expected", test_path_split_data)
def test_path_split(value, expected):
    result = path_split(value)
    assert result == expected, f"(in value: {value})"


test_dict_lookup_data = [
    pytest.param("user.name", test_dict["user"]["name"], id="basic"),
    pytest.param("-", test_dict, id="no lookup"),
    pytest.param("user", test_dict["user"], id="single"),
]


@pytest.mark.parametrize("value,expected", test_dict_lookup_data)
def test_dict_lookup(value, expected):
    result = dict_lookup(test_dict, value)
    assert result == expected, f"(in value: {value})"


test_iter_json_file_data = [
    pytest.param((path / "data" / "users.json", "-"), lambda data: len(data) == 10),
    pytest.param((path / "data" / "photos.json", "items"), lambda data: len(data) == 5000),
]


@pytest.mark.parametrize("value,expected", test_iter_json_file_data)
def test_iter_json_file(value, expected):
    result = list(iter_json_file(*value))
    assert expected(result) is True, f"(in value: {value})"


def test_safe_json_load():
    assert safe_json_load(path / "data" / "users.json")


abs_path = path.absolute()
abs_path_str = str(abs_path).replace("\\", "/")
# noinspection PyRedeclaration
test_process_path_data = [
    pytest.param(
        abs_path / "data" / "dummy_files" / "test1.txt",
        {abs_path_str + "/data/dummy_files/test1.txt"},
        id="single_file"
    ),
    pytest.param(
        abs_path / "data" / "dummy_files" / "*.txt",
        {abs_path_str + f"/data/dummy_files/test{i}.txt" for i in range(1, 4)},
        id="pattern"
    ),
    pytest.param(
        abs_path / "data" / "dummy_files" / "*.csv",
        {abs_path_str + f"/data/dummy_files/test{i}.csv" for i in range(1, 3)},
        id="pattern_2"
    ),
    pytest.param(
        abs_path / "data" / "*" / "*",
        {abs_path_str + f"/data/dummy_files/test{i}.txt" for i in range(1, 4)} |
        {abs_path_str + f"/data/dummy_files/test{i}.csv" for i in range(1, 3)},
        id="pattern_3"
    ),
    pytest.param(
        Path("*.py"),
        {p.replace("\\", "/")
         for p in map(str, Path('.').iterdir())
         if p.endswith(".py")},
        id="pattern_4"
    )
]


@pytest.mark.parametrize("value,expected", test_process_path_data)
def test_process_path(value, expected):
    result = set(str(p).replace("\\", "/") for p in _process_path(value))
    assert result == expected, f"(in value: {value})"
