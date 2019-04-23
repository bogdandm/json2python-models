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

## Installation

<aside class="warning">
**Be ware**: it supports only `python3.7` and higher.
</aside>

To install Requests, use `pip`:

`pip install`

Or you can build it from source:

```
git clone https://github.com/bogdandm/json2python-models.git
cd json2python-models
python setup.py install
```


## Tests

To run tests you should clone project and install `pytest` and `requests` (to download online datasets):

```
git clone https://github.com/bogdandm/json2python-models.git
cd json2python-models
pip install pytest>=4.4.0

python setup.py test -a '<pytest arguments>'
or
pytest tests
```

Also I would recommend you to install `pytest-xdist` for parallel execution 
and `pytest-sugar` for pretty printing test results

### Test examples

> 

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
3. All existing tests should be passed (including test examples)
4. Use `typing` module
5. Fix [codacy](https://app.codacy.com/project/bogdandm/json2python-models/dashboard) issues

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details
