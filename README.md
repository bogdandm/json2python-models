[![json2python-models](/etc/logo.png)](https://github.com/bogdandm/json2python-models)

[![PyPI version](https://badge.fury.io/py/json2python-models.svg)](https://badge.fury.io/py/json2python-models)
[![Build Status](https://travis-ci.org/bogdandm/json2python-models.svg?branch=master)](https://travis-ci.org/bogdandm/json2python-models)
[![Coverage Status](https://coveralls.io/repos/github/bogdandm/json2python-models/badge.svg?branch=master)](https://coveralls.io/github/bogdandm/json2python-models?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/11e13f2b81d7450eb0bca4b941d16d81)](https://www.codacy.com/app/bogdandm/json2python-models?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=bogdandm/json2python-models&amp;utm_campaign=Badge_Grade)

![Example](/etc/convert.png)

json2python-models is a [Python](https://www.python.org/) tool that can generate Python models classes 
(dataclasses, attrs) from JSON dataset. 

## Features

* Full `typing` module support
* Types merging - if some field could contains data of different types it will handle it
* Fields and models names generation (unicode support included)
* Similar models generalization
* Handling recursive data structures (i.e family tree)
* Detecting string literals (i.e. datetime or just stringify numbers)
* Generation models as tree (nested models) or list
* Specifying when dictionaries should be processed as is
* CLI tool

## Examples
[*skip*](#installation)

```json
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
            {
                "position": "2",
                "positionText": "2",
                "points": "62",
                "wins": "1",
                "Driver": {
                    "driverId": "bottas",
                    "permanentNumber": "77",
                    "code": "BOT",
                    "url": "http://en.wikipedia.org/wiki/Valtteri_Bottas",
                    "givenName": "Valtteri",
                    "familyName": "Bottas",
                    "dateOfBirth": "1989-08-28",
                    "nationality": "Finnish"
                },
                "Constructors": [
                    {
                        "constructorId": "mercedes",
                        "url": "http://en.wikipedia.org/wiki/Mercedes-Benz_in_Formula_One",
                        "name": "Mercedes",
                        "nationality": "German"
                    }
                ]
            }
        ]
    }
]
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

To install Requests, use `pip`:

`pip install`

Or you can build it from source:

```
git clone https://github.com/bogdandm/json2python-models.git
cd json2python-models
python setup.py install
```

## Usage

### CLI

> Coming soon

### Low level

> Coming soon (Wiki)

## Tests

To run tests you should clone project and install `pytest` and `requests` (to download online datasets):

```
git clone https://github.com/bogdandm/json2python-models.git
cd json2python-models

python setup.py test -a '<pytest additional arguments>'
```

Also I would recommend you to install `pytest-sugar` for pretty printing test results

### Test examples

You can find out some examples of usage of this project at [testing_tools/real_apis/...](/testing_tools/real_apis)

Each file contains functions to download data from some online API (references included at the top of file) and
`main` function that generate and print code. Some examples may print debug data before actual code.
Downloaded data will be saved at `testing_tools/real_apis/<name of example>/<dataset>.json`

## API docs

> Coming soon (Wiki)

## Built With

* [python-dateutil](https://github.com/dateutil/dateutil) - Datetime parsing
* [inflection](https://github.com/jpvanhal/inflection) - String transformations
* [Unidecode](https://pypi.org/project/Unidecode/) - Unicode to ASCII conversion
* [Jinja2](https://github.com/pallets/jinja) - Code templates
* [ordered-set](https://github.com/LuminosoInsight/ordered-set) is used in models merging algorithm

## Contributing

Feel free to open pull requests with new features or bug fixes. Just follow few rules:

1. Always use some code formatter ([black](https://github.com/ambv/black) or PyCharm built-in)
2. Keep code coverage above 95-98%
3. All existing tests should be passed (including test examples from `testing_tools/real_apis`)
4. Use `typing` module
5. Fix [codacy](https://app.codacy.com/project/bogdandm/json2python-models/dashboard) issues from your PR

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
