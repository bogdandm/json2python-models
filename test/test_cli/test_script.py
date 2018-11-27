import json
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from time import time

import pytest
import requests

tmp_dir = tempfile.TemporaryDirectory(f"-pytest-{time()}")
tmp_path = Path(tmp_dir.name)
test_data_path = (Path(__file__) / ".." / "data").resolve().absolute()
if not test_data_path.exists():
    test_data_path = Path("./test/test_cli/data").resolve().absolute()
    if not test_data_path.exists():
        test_data_path = None


# Create fixture to auto cleanup tmp directory after tests
@pytest.fixture(scope="session", autouse=True)
def tmp_dir_cleanup():
    yield tmp_dir
    tmp_dir.cleanup()


# download GitHub Gist dataset into tmp folder
GISTS_URL = "https://api.github.com/gists"
gists = requests.get(GISTS_URL).json()
for item in gists:
    with (tmp_path / f"{item['id']}.gist").open("w") as f:
        json.dump(item, f)
del gists

# detect script path
setuptools_script = subprocess.call(["json2models"], shell=True) == 0
if setuptools_script:
    executable = "json2models"
else:
    python_path = sys.executable.replace('\\', '/')
    executable = f"{python_path} -m json_to_models"


def test_help():
    c = f"{executable} -h"
    proc = subprocess.Popen(shlex.split(c), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    assert not stderr, stderr
    assert stdout, stdout
    assert proc.returncode == 0
    print(stdout.decode())


if test_data_path:
    mark_test_data = {}
else:
    mark_test_data = {"mark": pytest.mark.xfail}

test_commands = [
    pytest.param(f"""{executable} -l Photo items "{test_data_path / 'photos.json'}" """, id="list1", **mark_test_data),
    pytest.param(f"""{executable} -l User - "{test_data_path / 'users.json'}" """, id="list2", **mark_test_data),
    pytest.param(f"""{executable} -m Photos "{test_data_path / 'photos.json'}" """, id="model1", **mark_test_data),

    pytest.param(f"""{executable} -l Photo items "{test_data_path / 'photos.json'}" 
                                  -m Photos "{test_data_path / 'photos.json'}" """,
                 id="list1_model1", **mark_test_data),

    pytest.param(f"""{executable} -l Photo items "{test_data_path / 'photos.json'}" 
                                  -l User - "{test_data_path / 'users.json'}" """,
                 id="list1_list2", **mark_test_data),

    pytest.param(f"""{executable} -m Gist "{tmp_path / '*.gist'}" """, id="gists"),
    pytest.param(f"""{executable} -m Gist "{tmp_path / '*.gist'}" --datetime""", id="gists_datetime"),
    pytest.param(f"""{executable} -m Gist "{tmp_path / '*.gist'}" --merge percent number_10""",
                 id="gists_merge_policy"),
    pytest.param(f"""{executable} -m Gist "{tmp_path / '*.gist'}" --merge exact""",
                 id="gists_no_merge"),
]


@pytest.mark.parametrize("command", test_commands)
def test_script(command):
    print("Command:", command)
    proc = subprocess.Popen(shlex.split(command), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = proc.communicate()
    assert not stderr, stderr
    assert stdout, stdout
    assert proc.returncode == 0
    print(stdout.decode())


@pytest.mark.parametrize("command", test_commands)
def test_script_attrs(command):
    command += " -f attrs"
    print("Command:", command)
    proc = subprocess.Popen(shlex.split(command), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = map(bytes.decode, proc.communicate())
    assert not stderr, stderr
    assert stdout, stdout
    assert proc.returncode == 0
    assert "@attr.s" in stdout
    print(stdout)


@pytest.mark.parametrize("command", test_commands)
def test_script_custom(command):
    command += " -f custom --code-generator json_to_models.models.attr.AttrsModelCodeGenerator"
    command += ' --code-generator-kwargs "meta=true"'
    print("Command:", command)
    proc = subprocess.Popen(shlex.split(command), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = map(bytes.decode, proc.communicate())
    assert not stderr, stderr
    assert stdout, stdout
    assert proc.returncode == 0
    assert "@attr.s" in stdout
    print(stdout)


wrong_arguments_commands = [
    pytest.param(f"""{executable} -l Model items "{test_data_path / 'photos.json'}"
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
    proc = subprocess.Popen(shlex.split(command), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = map(bytes.decode, proc.communicate())
    assert not stderr and proc.returncode == 0, stderr
