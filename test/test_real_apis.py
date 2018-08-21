import pytest


@pytest.mark.no_expected
@pytest.mark.slow_http
def test_openlibrary():
    from testing_tools.real_apis.openlibrary import main
    main()