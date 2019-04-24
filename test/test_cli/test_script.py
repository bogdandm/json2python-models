import imp
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from time import time
from typing import Tuple

import pytest

tmp_dir = tempfile.TemporaryDirectory(f"-pytest-{time()}")
tmp_path = Path(tmp_dir.name)
test_data_path = (Path(__file__) / ".." / "data").resolve().absolute()
if not test_data_path.exists():
    test_data_path = Path("./test/test_cli/data").resolve().absolute()


# Create fixture to auto cleanup tmp directory after tests
@pytest.fixture(scope="session", autouse=True)
def tmp_dir_cleanup():
    yield tmp_dir
    tmp_dir.cleanup()


# download GitHub Gist dataset into tmp folder
with (test_data_path / "gists.json").open("r") as f:
    gists = json.load(f)
assert type(gists) is list and gists and type(gists[0]) is dict

for item in gists:
    with (tmp_path / f"{item['id']}.gist").open("w") as f:
        json.dump(item, f)

# detect script path
setuptools_script = subprocess.call(["json2models"], shell=True) == 0
if setuptools_script:
    executable = "json2models"
else:
    python_path = sys.executable.replace('\\', '/')
    executable = f"{python_path} -m json_to_models"


def test_help():
    c = f"{executable} -h"
    proc = subprocess.Popen(c, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    assert not stderr, stderr
    assert stdout, stdout
    assert proc.returncode == 0
    print(stdout.decode())


test_commands = [
    pytest.param(f"""{executable} -l Photo items "{test_data_path / 'photos.json'}" """, id="list1"),
    pytest.param(f"""{executable} -l User - "{test_data_path / 'users.json'}" """, id="list2"),
    pytest.param(f"""{executable} -m Photos "{test_data_path / 'photos.json'}" """, id="model1"),

    pytest.param(f"""{executable} -l Photo items "{test_data_path / 'photos.json'}" \
                                  -m Photos "{test_data_path / 'photos.json'}" """,
                 id="list1_model1"),

    pytest.param(f"""{executable} -l Photo items "{test_data_path / 'photos.json'}" \
                                  -l User - "{test_data_path / 'users.json'}" """,
                 id="list1_list2"),

    pytest.param(f"""{executable} -m Gist "{tmp_path / '*.gist'}" --dkf files""", id="gists"),
    pytest.param(f"""{executable} -m Gist "{tmp_path / '*.gist'}" --dkf files --datetime""", id="gists_datetime"),
    pytest.param(f"""{executable} -m Gist "{tmp_path / '*.gist'}" --dkf files --merge percent number_10""",
                 id="gists_merge_policy"),
    pytest.param(f"""{executable} -m Gist "{tmp_path / '*.gist'}" --dkf files --merge exact""",
                 id="gists_no_merge"),
    pytest.param(f"""{executable} -m Gist "{tmp_path / '*.gist'}" --dkf files --datetime --strings-converters""",
                 id="gists_strings_converters"),

    pytest.param(f"""{executable} -l User - "{test_data_path / 'users.json'}" --strings-converters""",
                 id="users_strings_converters"),
]


def _validate_result(proc: subprocess.Popen) -> Tuple[str, str]:
    stdout, stderr = map(bytes.decode, proc.communicate())
    assert not stderr, stderr
    assert stdout, stdout
    assert proc.returncode == 0
    # Note: imp package is deprecated but I can't find a way to create dummy module using importlib
    module = imp.new_module("test_model")
    sys.modules["test_model"] = module
    exec(compile(stdout, "test_model.py", "exec"), module.__dict__)
    return stdout, stderr


@pytest.mark.parametrize("command", test_commands)
def test_script(command):
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = _validate_result(proc)
    print(stdout)


@pytest.mark.parametrize("command", test_commands)
def test_script_flat(command):
    command += " -s flat"
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = _validate_result(proc)
    print(stdout)


@pytest.mark.parametrize("command", test_commands)
def test_script_attrs(command):
    command += " -f attrs"
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = _validate_result(proc)
    assert "@attr.s" in stdout
    print(stdout)


@pytest.mark.parametrize("command", test_commands)
def test_script_dataclasses(command):
    command += " -f dataclasses"
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = _validate_result(proc)
    assert "@dataclass" in stdout
    print(stdout)


@pytest.mark.parametrize("command", test_commands)
def test_script_custom(command):
    command += " -f custom --code-generator json_to_models.models.attr.AttrsModelCodeGenerator"
    command += ' --code-generator-kwargs "meta=true"'
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = _validate_result(proc)
    assert "@attr.s" in stdout
    print(stdout)


wrong_arguments_commands = [
    pytest.param(f"""{executable} -l Model items "{test_data_path / 'photos.json'}" \
                                  -l Model - "{test_data_path / 'users.json'}" """, id="duplicate_name"),
    pytest.param(f"""{executable} -l Model items "{test_data_path / 'photos.json'}" --merge unknown""",
                 id="wrong_merge_policy"),
    pytest.param(f"""{executable} -l Model items "{test_data_path / 'photos.json'}" --merge unknown_10""",
                 id="wrong_merge_policy"),
    pytest.param(f"""{executable} -l Model items "{test_data_path / 'photos.json'}" -f custom""",
                 id="custom_model_generator_without_class_link"),
    pytest.param(f"""{executable} -l Model items "{test_data_path / 'photos.json'}" --code-generator test""",
                 id="class_link_without_custom_model_generator_enabled"),
]


@pytest.mark.xfail
@pytest.mark.parametrize("command", wrong_arguments_commands)
def test_wrong_arguments(command):
    print("Command:", command)
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _validate_result(proc)
