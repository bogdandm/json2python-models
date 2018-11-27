import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

import json_to_models

with open('requirements.txt') as f:
    required = f.read().splitlines()
URL = "https://github.com/bogdandm/json2python-models"


class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ""

    def run_tests(self):
        import shlex
        import pytest

        errno = pytest.main(shlex.split(self.pytest_args + ' -m "not slow_http"'))
        sys.exit(errno)


setup(
    name="json2python-models",
    version=json_to_models.__version__,
    python_requires=">=3.7",
    url=URL,
    author="bogdandm (Bogdan Kalashnikov)",
    description="Python models (attrs, dataclasses or custom) generator from JSON data with typing module support",
    license="MIT",
    packages=find_packages(exclude=['test', 'testing_tools']),
    entry_points={
        'console_scripts': ['json2models = json_to_models.cli:main']
    },
    install_requires=required,
    cmdclass={"test": PyTest},
    tests_require=["pytest", "requests"],
    project_urls={
        'Source': URL
    },
    data_files=[('', ['pytest.ini', '.coveragerc', 'LICENSE'])]
)
