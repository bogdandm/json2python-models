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

    pytest.param(f"""{executable} -m Gist "{tmp_path / '*.gist'}" --dkf files""",
                 id="gists"),
    pytest.param(f"""{executable} -m Gist "{tmp_path / '*.gist'}" --dkf files --datetime""",
                 id="gists_datetime"),
    pytest.param(f"""{executable} -m Gist "{tmp_path / '*.gist'}" --dkf files --merge percent number_10""",
                 id="gists_merge_policy"),
    pytest.param(f"""{executable} -m Gist "{tmp_path / '*.gist'}" --dkf files --merge exact""",
                 id="gists_no_merge"),
    pytest.param(f"""{executable} -m Gist "{tmp_path / '*.gist'}" --dkf files --datetime --strings-converters""",
                 id="gists_strings_converters"),

    pytest.param(f"""{executable} -l User - "{test_data_path / 'users.json'}" --strings-converters""",
                 id="users_strings_converters"),
    pytest.param(f"""{executable} -m SomeUnicode "{test_data_path / 'unicode.json'}" """,
                 id="convert_unicode"),
    pytest.param(f"""{executable} -m SomeUnicode "{test_data_path / 'unicode.json'}" --no-unidecode""",
                 id="dont_convert_unicode"),
    pytest.param(f"""{executable} -m SomeUnicode "{test_data_path / 'unicode.json'}" --disable-unicode-conversion""",
                 id="dont_convert_unicode_2"),
    pytest.param(f"""{executable} -m YamlFile "{test_data_path / 'spotify-swagger.yaml'}" -i yaml""",
                 id="yaml_file"),
    pytest.param(f"""{executable} -m IniFile "{test_data_path / 'file.ini'}" -i ini""",
                 id="ini_file"),
]


def execute_test(command, output_file: Path = None, output=None) -> Tuple[str, str]:
    proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = map(bytes.decode, proc.communicate())
    if output_file:
        assert output is None
        with output_file.open(encoding='utf-8') as f:
            output = f.read()
    if output:
        stdout = output
    assert not stderr, stderr
    assert stdout, stdout
    assert proc.returncode == 0
    # Note: imp package is deprecated but I can't find a way to create dummy module using importlib
    module = imp.new_module("test_model")
    sys.modules["test_model"] = module
    try:
        exec(compile(stdout, "test_model.py", "exec"), module.__dict__)
    except Exception as e:
        assert not e, stdout

    print(stdout)
    return stdout


@pytest.mark.parametrize("command", test_commands)
def test_script(command):
    execute_test(command)


@pytest.mark.parametrize("command", test_commands)
def test_script_flat(command):
    command += " -s flat"
    execute_test(command)


@pytest.mark.parametrize("command", test_commands)
def test_script_attrs(command):
    command += " -f attrs"
    stdout = execute_test(command)
    assert "@attr.s" in stdout


@pytest.mark.parametrize("command", test_commands)
def test_script_pydantic(command):
    command += " -f pydantic"
    # Pydantic has native (str) -> (builtin_type) converters
    command = command.replace('--strings-converters', '')
    stdout = execute_test(command)
    assert "(BaseModel):" in stdout


@pytest.mark.parametrize("command", test_commands)
def test_script_pydantic_disable_literals(command):
    command += " -f pydantic --code-generator-kwargs max_literals=0"
    # Pydantic has native (str) -> (builtin_type) converters
    command = command.replace('--strings-converters', '')
    stdout = execute_test(command)
    assert "(BaseModel):" in stdout
    assert "Literal" not in stdout


@pytest.mark.parametrize("command", test_commands)
def test_script_dataclasses(command):
    command += " -f dataclasses"
    stdout = execute_test(command)
    assert "@dataclass" in stdout


@pytest.mark.parametrize("command", test_commands)
def test_script_custom(command):
    command += " -f custom --code-generator json_to_models.models.attr.AttrsModelCodeGenerator"
    command += ' --code-generator-kwargs "meta=true"'
    stdout = execute_test(command)
    assert "@attr.s" in stdout


@pytest.mark.parametrize("command", test_commands)
def test_add_preamble(command):

    PREAMBLE_TEXT = """
# this is some test code
# to be added to the file


# let's see if it works


    """
    stdout = execute_test(command + ' --preamble "' + PREAMBLE_TEXT + '"')
    assert "let's see if it works" in stdout


@pytest.mark.parametrize("command", test_commands)
def test_add_trim_preamble(command):

    def trim_header(line_string):
        """remove the quoted command and everything from the first class declaration onwards"""
        lines = line_string.splitlines()
        start = 0
        end = 0
        line_no = 0
        for l in lines:
            if l.startswith('"""'):
                start = line_no
            if l.startswith('class '):
                end = line_no
                break
            line_no += 1

        return lines[start:end]

    expected_result = execute_test(command)

    BLANK_SPACE = """




        """
    # ensure blank space does not get propagated
    stdout = execute_test(command + ' --preamble "' + BLANK_SPACE + '"')

    assert trim_header(expected_result) == trim_header(stdout)


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
    execute_test(command)


@pytest.mark.parametrize("command", test_commands)
def test_script_output_file(command):
    file = tmp_path / 'out.py'
    command += f" -o {file}"
    execute_test(command, output_file=file)
