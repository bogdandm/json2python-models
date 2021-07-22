import multiprocessing
import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

import json_to_models

REPO = "bogdandm/json2python-models"
CPU_N = multiprocessing.cpu_count()

with open('requirements.txt') as f:
    required = f.read().splitlines()
with open('README.md') as f:
    long_description = f.read()
long_description = long_description.replace("/etc", f"https://raw.githubusercontent.com/{REPO}/master/etc")


class PyTest(TestCommand):
    user_options = [("pytest-args=", "a", "Arguments to pass to pytest")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = ""

    def run_tests(self):
        import shlex
        import pytest
        args = self.pytest_args
        if CPU_N > 1 and "-n " not in args:
            args += f" -n {CPU_N}"
        errno = pytest.main(shlex.split(args))
        sys.exit(errno)


setup(
    name="json2python-models",
    version=json_to_models.__version__,
    python_requires=">=3.7",
    url=f"https://github.com/{REPO}",
    author="bogdandm (Bogdan Kalashnikov)",
    author_email="bogdan.dm1995@yandex.ru",
    description="Python models (pydantic, attrs, dataclasses or custom) generator from JSON data with typing module support",
    long_description=long_description,
    long_description_content_type='text/markdown',
    license="MIT",
    packages=find_packages(exclude=['test', 'testing_tools']),
    entry_points={
        'console_scripts': ['json2models = json_to_models.cli:main']
    },
    install_requires=required,
    cmdclass={"test": PyTest},
    tests_require=["pytest>=4.4.0", "pytest-xdist", "requests", "attrs", "pydantic>=1.3", "ruamel.yaml"],
    data_files=[('', ['requirements.txt', 'pytest.ini', '.coveragerc', 'LICENSE', 'README.md', 'CHANGELOG.md'])]
)
