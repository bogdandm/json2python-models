[![json2python-models](/etc/logo.png)](https://github.com/bogdandm/json2python-models)

[![PyPI version](https://badge.fury.io/py/json2python-models.svg)](https://badge.fury.io/py/json2python-models)
[![Build Status](https://travis-ci.org/bogdandm/json2python-models.svg?branch=master)](https://travis-ci.org/bogdandm/json2python-models)
[![Coverage Status](https://coveralls.io/repos/github/bogdandm/json2python-models/badge.svg?branch=master)](https://coveralls.io/github/bogdandm/json2python-models?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/11e13f2b81d7450eb0bca4b941d16d81)](https://www.codacy.com/app/bogdandm/json2python-models?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=bogdandm/json2python-models&amp;utm_campaign=Badge_Grade)

![Example](/etc/convert.png)

json2python-models is a [Python](https://www.python.org/) tool that can generate Python models classes 
(dataclasses, [attrs](https://github.com/python-attrs/attrs)) from JSON dataset. 

## Features

* Full **`typing` module** support
* **Types merging** - if some field contains data of different types this will be represent as `Union` type
* Fields and models **names** generation (unicode support included)
* Similar **models generalization**
* Handling **recursive data** structures (i.e family tree)
* Detecting **string literals** (i.e. datetime or just stringify numbers) 
    and providing decorators to easily convert into Python representation
* Generation models as **tree** (nested models) or **list**
* Specifying when dictionaries should be processed as **`dict` type** (by default every dict is considered as some model)
* **CLI** tool

## Table of Contents

* [Features](#features)
* [Table of Contents](#table-of-contents)
* [Example](#example)
* [Installation](#installation)
* [Usage](#usage)
    * [CLI](#cli)
    * [Low level API]()
* [Tests](#tests)
    * [Test examples](#test-examples)
* [Built With](#built-with)
* [Contributing](#contributing)
* [License](#license)

## Example

```
driver_standings.json
[
    {
        "season": "2019",
        "round": "3",
        "DriverStandings": [
            {
                "position": "1",
                "positionText": "1",
                "points": "68",
                "wins": "2",
                "Driver": {
                    "driverId": "hamilton",
                    "permanentNumber": "44",
                    "code": "HAM",
                    "url": "http://en.wikipedia.org/wiki/Lewis_Hamilton",
                    "givenName": "Lewis",
                    "familyName": "Hamilton",
                    "dateOfBirth": "1985-01-07",
                    "nationality": "British"
                },
                "Constructors": [
                    {
                        "constructorId": "mercedes",
                        "url": "http://en.wikipedia.org/wiki/Mercedes-Benz_in_Formula_One",
                        "name": "Mercedes",
                        "nationality": "German"
                    }
                ]
            },
            ...
        ]
    }
]
```

```
json2models -f attrs -l DriverStandings driver_standings.json
```

```python
import attr
from json_to_models.dynamic_typing import IntString, IsoDateString
from typing import List


@attr.s
class DriverStandings:
    @attr.s
    class DriverStanding:
        @attr.s
        class Driver:
            driver_id: str = attr.ib()
            permanent_number: IntString = attr.ib(converter=IntString)
            code: str = attr.ib()
            url: str = attr.ib()
            given_name: str = attr.ib()
            family_name: str = attr.ib()
            date_of_birth: IsoDateString = attr.ib(converter=IsoDateString)
            nationality: str = attr.ib()
    
        @attr.s
        class Constructor:
            constructor_id: str = attr.ib()
            url: str = attr.ib()
            name: str = attr.ib()
            nationality: str = attr.ib()
    
        position: IntString = attr.ib(converter=IntString)
        position_text: IntString = attr.ib(converter=IntString)
        points: IntString = attr.ib(converter=IntString)
        wins: IntString = attr.ib(converter=IntString)
        driver: 'Driver' = attr.ib()
        constructors: List['Constructor'] = attr.ib()

    season: IntString = attr.ib(converter=IntString)
    round: IntString = attr.ib(converter=IntString)
    driver_standings: List['DriverStanding'] = attr.ib()
```

## Installation

| **Be ware**: this project supports only `python3.7` and higher. |
| --- |

To install it, use `pip`:

`pip install json2python-models`

Or you can build it from source:

```
git clone https://github.com/bogdandm/json2python-models.git
cd json2python-models
python setup.py install
```

## Usage

### CLI

For regular usage CLI tool is the best option. After you install this package you could use it as `json2models <arguments>` 
or `python -m json_to_models <arguments>`. I.e.:
```
json2models -m Car car_*.json -f attrs > car.py
```

Arguments:
* `-h`, `--help` - Show help message and exit
    
* `-m`, `--model` - Model name and its JSON data as path or unix-like path pattern. `*`,  `**` or `?` patterns symbols are supported.
    * **Format**: `-m <Model name> [<JSON files> ...]`
    * **Example**: `-m Car audi.json reno.json` or `-m Car audi.json -m Car reno.json` (results will be the same)
    
* `-l`, `--list` - Like `-m` but given json file should contain list of model data (dataset). 
    If this file contains dict with nested list than you can pass `<JSON key>` to lookup. 
    Deep lookups are supported by dot-separated path. If no lookup needed pass `-` as `<JSON key>`.
    * **Format**: `-l <Model name> <JSON key> <JSON file>`
    * **Example**: `-l Car - cars.json -l Person fetch_results.items.persons result.json`
    * **Note**: Models names under this arguments should be unique.
    
* `-f`, `--framework` - Model framework for which python code is generated. 
    `base` (default) mean no framework so code will be generated without any decorators and additional meta-data.
    * **Format**: `-f {base,attrs,dataclasses,custom}`
    * **Example**: `-f attrs`
    * **Default**: `-f base`
    
* `-s , --structure` - Models composition style.
    * **Format**: `-s {nested, flat}` 
    * **Example**: `-s flat`
    * **Default**: `-s nested`
    
* `--datetime` - Enable datetime/date/time strings parsing.
    * **Default**: disabled
    * **Warning**: This can lead to 6-7 times slowdown on large datasets. Be sure that you really need this option.
    
* `--strings-converters` - Enable generation of string types converters (i.e. `IsoDatetimeString` or `BooleanString`).
    * **Default**: disabled

* `--merge` - Merge policy settings. Possible values are: 
    * **Format**: `--merge MERGE_POLICY [MERGE_POLICY ...]`
    * **Possible values** (MERGE_POLICY):
        * `percent[_<percent>]` - two models had a certain percentage of matched field names. 
            Custom value could be i.e. `percent_95`. 
        * `number[_<number>]` - two models had a certain number of matched field names. 
        * `exact` - two models should have exact same field names to merge.
    * **Example**: `--merge percent_95 number_20` - merge if 95% of fields are matched or 20 of fields are matched
    * **Default**: `--merge percent_70 number_10`
    
* `--dict-keys-regex`, `--dkr` - List of regular expressions (Python syntax).
    If all keys of some dict are match one of the pattern then 
    this dict will be marked as dict field but not nested model.
    * **Format**: `--dkr RegEx [RegEx ...]`
    * **Example**: `--dkr node_\d+ \d+_\d+_\d+`
    * **Note**: `^` and `$` (string borders) tokens will be added automatically but you 
        have escape to other special characters manually.
    * **Optional**
    
* `--dict-keys-fields`, `--dkf` - List of model fields names that will be marked as dict fields
    * **Format**: `--dkf FIELD_NAME [FIELD_NAME ...]`
    * **Example**: `--dkf "dict_data" "mapping"`
    * **Optional**
    
* `--code-generator` - Absolute import path to `GenericModelCodeGenerator` subclass.
    * **Format**: `--code-generator CODE_GENERATOR`
    * **Example**: `-f mypackage.mymodule.DjangoModelsGenerator`
    * **Note**: Is ignored without `-f custom` but is required with it.
    
* `--code-generator-kwargs` - List of GenericModelCodeGenerator subclass arguments (for `__init__` method, 
    see docs of specific subclass). 
    Each argument should be in following format: `argument_name=value` or `"argument_name=value with space"`. 
    Boolean values should be passed in JS style: `true` or `false`
    * **Format**: `--code-generator-kwargs [NAME=VALUE [NAME=VALUE ...]]`
    * **Example**:  `--code-generator-kwargs kwarg1=true kwarg2=10 "kwarg3=It is string with spaces"`
    * **Optional**

One of model arguments (`-m` or `-l`) is required.

### Low level API

> Coming soon (Wiki)

## Tests

To run tests you should clone project and run `setup.py` script:

```
git clone https://github.com/bogdandm/json2python-models.git
cd json2python-models
python setup.py test -a '<pytest additional arguments>'
```

Also I would recommend you to install `pytest-sugar` for pretty printing test results

### Test examples

You can find out some examples of usage of this project at [testing_tools/real_apis/...](/testing_tools/real_apis)

Each file contains functions to download data from some online API (references included at the top of file) and
`main` function that generates and prints code. Some examples may print debug data before actual code.
Downloaded data will be saved at `testing_tools/real_apis/<name of example>/<dataset>.json`

## Built With

* [python-dateutil](https://github.com/dateutil/dateutil) - Datetime parsing
* [inflection](https://github.com/jpvanhal/inflection) - String transformations
* [Unidecode](https://pypi.org/project/Unidecode/) - Unicode to ASCII conversion
* [Jinja2](https://github.com/pallets/jinja) - Code templates
* [ordered-set](https://github.com/LuminosoInsight/ordered-set) is used in models merging algorithm

Test tools:
* [pytest](https://github.com/pytest-dev/pytest) - Test framework
* [pytest-xdist](https://github.com/pytest-dev/pytest-xdist) - Parallel execution of test suites
* [pytest-sugar](https://github.com/Frozenball/pytest-sugar) - Test results pretty printing
* [requests](https://github.com/kennethreitz/requests) - Test data download

## Contributing

Feel free to open pull requests with new features or bug fixes. Just follow few rules:

1. Always use some code formatter ([black](https://github.com/ambv/black) or PyCharm built-in)
2. Keep code coverage above 95-98%
3. All existing tests should be passed (including test examples from `testing_tools/real_apis`)
4. Use `typing` module
5. Fix [codacy](https://app.codacy.com/project/bogdandm/json2python-models/dashboard) issues from your PR

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
