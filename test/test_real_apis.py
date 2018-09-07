import json

import pytest
import requests


# In this tests all network and JSON decode errors will be skipped
# so they will not be affected by network or API problems

# These are tests only for insurance because of synthetic tests may not cover some combinations of datatypes or values
# I will check output of tests bellow manually after major changes in core logic

@pytest.mark.no_expected
@pytest.mark.slow_http
def test_openlibrary():
    from testing_tools.real_apis.openlibrary import main
    try:
        main()
    except (OSError, requests.HTTPError, json.JSONDecodeError):
        pass


@pytest.mark.no_expected
@pytest.mark.slow_http
def test_f1():
    from testing_tools.real_apis.f1 import main
    try:
        main()
    except (OSError, requests.HTTPError, json.JSONDecodeError):
        pass


@pytest.mark.no_expected
@pytest.mark.slow_http
def test_randomapis():
    from testing_tools.real_apis.randomapis import main
    try:
        main()
    except (OSError, requests.HTTPError, json.JSONDecodeError):
        pass


@pytest.mark.no_expected
@pytest.mark.slow_http
def test_randomapis():
    from testing_tools.real_apis.pathofexile import main
    try:
        main()
    except (OSError, requests.HTTPError, json.JSONDecodeError):
        pass
