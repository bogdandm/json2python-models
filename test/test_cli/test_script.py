import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from test.test_cli.utils import create_module
from time import time

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
    with (tmp_path / f"{item['id']}.gist").open("w") as json_file:
        json.dump(item, json_file)

# detect script path
setuptools_script = subprocess.call(["json2models"], shell=True) == 0
if setuptools_script:
    executable = "json2models"
else:
    # python_path = sys.executable.replace("\\", "/")
    python_path = sys.executable
    executable = f"{python_path} -m json_to_models"


def test_help():
    c = f"{executable} -h"
    proc = subprocess.Popen(
        c, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = proc.communicate()
    assert not stderr, stderr
    assert stdout, stdout
    assert proc.returncode == 0
    print(stdout.decode())


test_commands = [
    pytest.param(
        f"{executable} -m Photo items {test_data_path / 'photos.json'}",
        id="list1",
    ),
    pytest.param(
        f"{executable}  -l Photo items {test_data_path / 'photos.json'}",
        id="list1_legacy",
    ),
    pytest.param(
        f"{executable}  -m User {test_data_path / 'users.json'}",
        id="list2",
    ),
    pytest.param(
        f"{executable}  -l User - {test_data_path / 'users.json'}",
        id="list2_legacy",
    ),
    pytest.param(
        f"{executable}  -m Photos {test_data_path / 'photos.json'}",
        id="model1",
    ),
    pytest.param(
        f"{executable} -m Model items {test_data_path / 'photos.json'} "
        f"-m Model {test_data_path / 'users.json'}",
        id="duplicate_name",
    ),
    pytest.param(
        f"{executable} -m Photo items {test_data_path / 'photos.json'} "
        f"-m Photos {test_data_path / 'photos.json'}",
        id="list1_model1",
    ),
    pytest.param(
        f"{executable}  -m Photo items {test_data_path / 'photos.json'} "
        f"-m User {test_data_path / 'users.json'}",
        id="list1_list2",
    ),
    pytest.param(
        f"{executable}  -m Gist {tmp_path / '*.gist'} --dkf files ",
        id="gists",
    ),
    pytest.param(
        f"{executable}  -m Gist {tmp_path / '*.gist'} --dkf files "
        f"--datetime ",
        id="gists_datetime",
    ),
    pytest.param(
        f"{executable}  -m Gist {tmp_path / '*.gist'} --dkf files "
        f"--merge percent number_10 ",
        id="gists_merge_policy",
    ),
    pytest.param(
        f"{executable}  -m Gist {tmp_path / '*.gist'} --dkf files "
        f"--merge exact ",
        id="gists_no_merge",
    ),
    pytest.param(
        f"{executable}  -m Gist {tmp_path / '*.gist'} --dkf files "
        f"--datetime --strings-converters ",
        id="gists_strings_converters",
    ),
    pytest.param(
        f"{executable}  -m User {test_data_path / 'users.json'} "
        f"--strings-converters",
        id="users_strings_converters",
    ),
    pytest.param(
        f"{executable} -m SomeUnicode {test_data_path / 'unicode.json'}",
        id="convert_unicode",
    ),
    pytest.param(
        f"{executable}  -m SomeUnicode {test_data_path / 'unicode.json'} "
        f"--no-unidecode",
        id="dont_convert_unicode",
    ),
    pytest.param(
        f"{executable} -m SomeUnicode {test_data_path / 'unicode.json'} "
        f"--disable-unicode-conversion",
        id="dont_convert_unicode_2",
    ),
    pytest.param(
        f"{executable} -m YamlFile {test_data_path / 'spotify-swagger.yaml'} "
        f"-i yaml",
        id="yaml_file",
    ),
    pytest.param(
        f"{executable} -m IniFile {test_data_path / 'file.ini'} -i ini ",
        id="ini_file",
    ),
]


def execute_test(command, output_file: Path = None, output=None) -> str:
    proc = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = map(
        lambda std_output: bytes.decode(std_output, errors="ignore"),
        proc.communicate(),
    )
    if output_file:
        assert output is None
        with output_file.open(encoding="utf-8", errors="ignore") as file_obj:
            output = file_obj.read()
    if output:
        stdout = output
    assert not stderr, stderr
    assert stdout, stdout
    assert proc.returncode == 0
    # Note: imp package is deprecated, but I can't find a way to create dummy
    # module using importlib
    module = create_module("test_model")
    sys.modules["test_model"] = module
    try:
        exec(compile(stdout, "test_model.py", "exec"), module.__dict__)
    except Exception as e:
        assert not e, stdout

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
    command = command.replace("--strings-converters", "")
    stdout = execute_test(command)
    assert "(BaseModel):" in stdout


@pytest.mark.parametrize("command", test_commands)
def test_script_pydantic_disable_literals(command):
    command += " -f pydantic --code-generator-kwargs max_literals=0"
    # Pydantic has native (str) -> (builtin_type) converters
    command = command.replace("--strings-converters", "")
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
    command += (
        " -f custom --code-generator "
        "json_to_models.models.attr.AttrsModelCodeGenerator"
    )
    command += ' --code-generator-kwargs "meta=true"'
    stdout = execute_test(command)
    assert "@attr.s" in stdout


@pytest.mark.parametrize("command", test_commands)
def test_add_preamble(command):
    PREAMBLE_TEXT = (
        "# this is some test code to be added to the file. Let's see if it "
        "works"
    )
    stdout = execute_test(command + ' --preamble "' + PREAMBLE_TEXT + '"')
    assert "let's see if it works" in stdout


@pytest.mark.parametrize("command", test_commands)
def test_disable_some_string_types_smoke(command):
    command += " --disable-str-serializable-types float int"
    execute_test(command)


@pytest.mark.parametrize("command", test_commands)
def test_add_trim_preamble(command):
    def trim_header(line_string):
        """
        remove the quoted command and everything from the first class
        declaration onwards
        Args:
            line_string:

        Returns:

        """
        lines = line_string.splitlines()
        start = 0
        end = 0
        line_no = 0
        for line in lines:
            if line.startswith('"'):
                start = line_no
            if line.startswith("class "):
                end = line_no
                break
            line_no += 1

        return lines[start:end]

    expected_result = execute_test(command)

    blank_space = """




        """
    # ensure blank space does not get propagated
    stdout = execute_test(command + ' --preamble "' + blank_space + '"')

    assert trim_header(expected_result) == trim_header(stdout)


wrong_arguments_commands = [
    pytest.param(
        f"{executable} -m Model items {test_data_path / 'photos.json'} "
        f"--merge unknown",
        id="wrong_merge_policy",
    ),
    pytest.param(
        f"{executable} -m Model items {test_data_path / 'photos.json'} "
        f"--merge unknown_10",
        id="wrong_merge_policy",
    ),
    pytest.param(
        f"{executable}  -m Model items {test_data_path / 'photos.json'} "
        f"-f custom",
        id="custom_model_generator_without_class_link",
    ),
    pytest.param(
        f"{executable}  -m Model items {test_data_path / 'photos.json'} "
        f"--code-generator test",
        id="class_link_without_custom_model_generator_enabled",
    ),
    pytest.param(
        f"{executable}  -m Model items {test_data_path / 'photos.json'} "
        f"another_arg --code-generator test",
        id="4_args_model",
    ),
    pytest.param(
        f"{executable}  -m Model total {test_data_path / 'photos.json'} "
        f"--code-generator test",
        id="non_dict_or_list_data",
    ),
]


@pytest.mark.xfail(strict=True)
@pytest.mark.parametrize("command", wrong_arguments_commands)
def test_wrong_arguments(command):
    print("Command:", command)
    execute_test(command)


@pytest.mark.parametrize("command", test_commands)
def test_script_output_file(command):
    file = tmp_path / "out.py"
    command += f" -o {file}"
    execute_test(command, output_file=file)


cmds = [
    pytest.param(
        f"{executable}  -m User {test_data_path / 'users.json'} -f "
        f"pydantic --disable-str-serializable-types float int",
        id="users",
    )
]


@pytest.mark.parametrize("command", cmds)
def test_disable_some_string_types(command):
    stdout = execute_test(command)
    assert "lat: str" in stdout
    assert "lng: str" in stdout
    assert not any(
        re.match(r"\s+zipcode:.+int.+", line) for line in stdout.split("\n")
    ), "zipcode should not be parsed as int"
