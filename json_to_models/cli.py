import argparse
import importlib
import itertools
import json
import os.path
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Iterable, List, Tuple, Type, Union

import json_to_models
from json_to_models.dynamic_typing import ModelMeta, register_datetime_classes
from json_to_models.generator import MetadataGenerator
from json_to_models.models import ModelsStructureType
from json_to_models.models.attr import AttrsModelCodeGenerator
from json_to_models.models.base import GenericModelCodeGenerator, generate_code
from json_to_models.models.dataclasses import DataclassModelCodeGenerator
from json_to_models.models.structure import compose_models, compose_models_flat
from json_to_models.registry import (
    ModelCmp, ModelFieldsEquals, ModelFieldsNumberMatch, ModelFieldsPercentMatch, ModelRegistry
)
from json_to_models.utils import convert_args

STRUCTURE_FN_TYPE = Callable[[Dict[str, ModelMeta]], ModelsStructureType]
bool_js_style = lambda s: {"true": True, "false": False}.get(s, None)


class Cli:
    MODEL_CMP_MAPPING = {
        "percent": convert_args(ModelFieldsPercentMatch, lambda s: float(s) / 100),
        "number": convert_args(ModelFieldsNumberMatch, int),
        "exact": ModelFieldsEquals
    }

    STRUCTURE_FN_MAPPING: Dict[str, STRUCTURE_FN_TYPE] = {
        "nested": compose_models,
        "flat": compose_models_flat
    }

    MODEL_GENERATOR_MAPPING: Dict[str, Type[GenericModelCodeGenerator]] = {
        "base": convert_args(GenericModelCodeGenerator),
        "attrs": convert_args(AttrsModelCodeGenerator, meta=bool_js_style),
        "dataclasses": convert_args(DataclassModelCodeGenerator, meta=bool_js_style, post_init_converters=bool_js_style)
    }

    def __init__(self):
        self.initialized = False
        self.models_data: Dict[str, Iterable[dict]] = {}  # -m/-l
        self.enable_datetime: bool = False  # --datetime
        self.strings_converters: bool = False  # --strings-converters
        self.merge_policy: List[ModelCmp] = []  # --merge
        self.structure_fn: STRUCTURE_FN_TYPE = None  # -s
        self.model_generator: Type[GenericModelCodeGenerator] = None  # -f & --code-generator
        self.model_generator_kwargs: Dict[str, Any] = None

        self.argparser = self._create_argparser()

    def parse_args(self, args: List[str] = None):
        """
        Parse list of command list arguments

        :param args: (Optional) List of arguments
        :return: None
        """
        parser = self.argparser
        namespace = parser.parse_args(args)

        # Extract args
        models: List[Tuple[str, Iterable[Path]]] = [
            (model_name, itertools.chain(*map(_process_path, paths)))
            for model_name, *paths in namespace.model or ()
        ]
        models_lists: List[Tuple[str, Tuple[str, Path]]] = [
            (model_name, (lookup, Path(path)))
            for model_name, lookup, path in namespace.list or ()
        ]
        self.enable_datetime = namespace.datetime
        self.strings_converters = namespace.strings_converters
        merge_policy = [m.split("_") if "_" in m else m for m in namespace.merge]
        structure = namespace.structure
        framework = namespace.framework
        code_generator = namespace.code_generator
        code_generator_kwargs_raw: List[str] = namespace.code_generator_kwargs
        dict_keys_regex: List[str] = namespace.dict_keys_regex
        dict_keys_fields: List[str] = namespace.dict_keys_fields

        self.validate(models, models_lists, merge_policy, framework, code_generator)
        self.setup_models_data(models, models_lists)
        self.set_args(merge_policy, structure, framework, code_generator, code_generator_kwargs_raw,
                      dict_keys_regex, dict_keys_fields)

    def run(self):
        if self.enable_datetime:
            register_datetime_classes()
        generator = MetadataGenerator(
            dict_keys_regex=self.dict_keys_regex,
            dict_keys_fields=self.dict_keys_fields
        )
        registry = ModelRegistry(*self.merge_policy)
        for name, data in self.models_data.items():
            meta = generator.generate(*data)
            registry.process_meta_data(meta, name)
        registry.merge_models(generator)
        registry.generate_names()
        structure = self.structure_fn(registry.models_map)
        return generate_code(structure, self.model_generator, class_generator_kwargs=self.model_generator_kwargs)

    def validate(self, models, models_list, merge_policy, framework, code_generator):
        """
        Validate parsed args

        :param models:  List of pairs (model name, list of filesystem path)
        :param models_list: List of pairs (model name, list of lookup expr and filesystem path)
        :param merge_policy: List of merge policies. Each merge policy is either string or string and policy arguments
        :param framework: Framework name (predefined code generator)
        :param code_generator: Code generator import string
        :return:
        """
        names = {name for name, _ in models_list}
        if len(names) != len(models_list):
            raise ValueError("Model names under -l flag should be unique")

        for m in merge_policy:
            if isinstance(m, list):
                if m[0] not in self.MODEL_CMP_MAPPING:
                    raise ValueError(f"Invalid merge policy '{m[0]}', choices are {self.MODEL_CMP_MAPPING.keys()}")
            elif m not in self.MODEL_CMP_MAPPING:
                raise ValueError(f"Invalid merge policy '{m}', choices are {self.MODEL_CMP_MAPPING.keys()}")

        if framework == 'custom' and code_generator is None:
            raise ValueError("You should specify --code-generator to support custom generator")
        elif framework != 'custom' and code_generator is not None:
            raise ValueError("--code-generator argument has no effect without '--framework custom' argument")

    def setup_models_data(self, models: Iterable[Tuple[str, Iterable[Path]]],
                          models_lists: Iterable[Tuple[str, Tuple[str, Path]]]):
        """
        Initialize lazy loaders for models data
        """
        models_dict: Dict[str, List[Iterable[dict]]] = defaultdict(list)
        for model_name, paths in models:
            models_dict[model_name].append(map(safe_json_load, paths))
        for model_name, (lookup, path) in models_lists:
            models_dict[model_name].append(iter_json_file(path, lookup))

        self.models_data = {
            model_name: itertools.chain(*list_of_gen)
            for model_name, list_of_gen in models_dict.items()
        }

    def set_args(self, merge_policy: List[Union[List[str], str]],
                 structure: str, framework: str, code_generator: str, code_generator_kwargs_raw: List[str],
                 dict_keys_regex: List[str], dict_keys_fields: List[str]):
        """
        Convert CLI args to python representation and set them to appropriate object attributes
        """
        self.merge_policy.clear()
        for merge in merge_policy:
            if isinstance(merge, str):
                name = merge
                args = ()
            else:
                name = merge[0]
                args = merge[1:]
            self.merge_policy.append(self.MODEL_CMP_MAPPING[name](*args))

        self.structure_fn = self.STRUCTURE_FN_MAPPING[structure]

        if framework != "custom":
            self.model_generator = self.MODEL_GENERATOR_MAPPING[framework]
        else:
            module, cls = code_generator.rsplit('.', 1)
            m = importlib.import_module(module)
            self.model_generator = getattr(m, cls)

        self.model_generator_kwargs = {} if not self.strings_converters else {'post_init_converters': True}
        if code_generator_kwargs_raw:
            for item in code_generator_kwargs_raw:
                if item[0] == '"':
                    item = item[1:]
                if item[-1] == '"':
                    item = item[:-1]
                name, value = item.split("=", 1)
                self.model_generator_kwargs[name] = value

        self.dict_keys_regex = [re.compile(rf"^{r}$") for r in dict_keys_regex] if dict_keys_regex else ()
        self.dict_keys_fields = dict_keys_fields or ()

        self.initialized = True

    @classmethod
    def _create_argparser(cls) -> argparse.ArgumentParser:
        """
        ArgParser factory
        """
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter,
            description="Convert given json files into Python models."
        )

        parser.add_argument(
            "-m", "--model",
            nargs="+", action="append", metavar=("<Model name>", "<JSON files>"),
            help="Model name and its JSON data as path or unix-like path pattern.\n"
                 "'*',  '**' or '?' patterns symbols are supported.\n\n"
        )
        parser.add_argument(
            "-l", "--list",
            nargs=3, action="append", metavar=("<Model name>", "<JSON key>", "<JSON file>"),
            help="Like -m but given json file should contain list of model data.\n"
                 "If this file contains dict with nested list than you can pass\n"
                 "<JSON key> to lookup. Deep lookups are supported by dot-separated path.\n"
                 "If no lookup needed pass '-' as <JSON key>\n\n"

                 "I.e. for file that contains dict {\"a\": {\"b\": [model_data, ...]}} you should\n"
                 "pass 'a.b' as <JSON key>.\n\n"
        )
        parser.add_argument(
            "-f", "--framework",
            default="base",
            choices=list(cls.MODEL_GENERATOR_MAPPING.keys()) + ["custom"],
            help="Model framework for which python code is generated.\n"
                 "'base' (default) mean no framework so code will be generated without any decorators\n"
                 "and additional meta-data.\n"
                 "If you pass 'custom' you should specify --code-generator argument\n\n"
        )
        parser.add_argument(
            "-s", "--structure",
            default="nested",
            choices=list(cls.STRUCTURE_FN_MAPPING.keys()),
            help="Models composition style. By default nested models become nested Python classes.\n\n"
        )
        parser.add_argument(
            "--datetime",
            action="store_true",
            help="Enable datetime/date/time strings parsing.\n"
                 "Warn.: This can lead to 6-7 times slowdown on large datasets.\n"
                 "       Be sure that you really need this option.\n\n"
        )
        parser.add_argument(
            "--strings-converters",
            action="store_true",
            help="Enable generation of string types converters (i.e. IsoDatetimeString or BooleanString).\n\n"
        )

        default_percent = f"{ModelFieldsPercentMatch.DEFAULT * 100:.0f}"
        default_number = f"{ModelFieldsNumberMatch.DEFAULT:.0f}"
        parser.add_argument(
            "--merge",
            default=["percent", "number"],
            nargs="+",
            help=f"Merge policy settings. Default is 'percent_{default_percent} number_{default_number}' (percent of field match\n"
                 "or number of fields match).\n"
                 "Possible values are:\n"
                 "'percent[_<percent>]' - two models had a certain percentage of matched field names.\n"
                 f"                        Default percent is {default_percent}%%. "
                 "Custom value could be i.e. 'percent_95'.\n"
                 "'number[_<number>]'   - two models had a certain number of matched field names.\n"
                 f"                        Default number of fields is {default_number}.\n"
                 "'exact'               - two models should have exact same field names to merge.\n\n"
        )
        parser.add_argument(
            "--dict-keys-regex", "--dkr",
            nargs="+", metavar="RegEx",
            help="List of regular expressions (Python syntax).\n"
                 "If all keys of some dict are match one of them\n"
                 "then this dict will be marked as dict field but not nested model.\n"
                 "Note: ^ and $ tokens will be added automatically but you have to\n"
                 "escape other special characters manually.\n"
        )
        parser.add_argument(
            "--dict-keys-fields", "--dkf",
            nargs="+", metavar="FIELD NAME",
            help="List of model fields names that will be marked as dict fields\n\n"
        )
        parser.add_argument(
            "--code-generator",
            help="Absolute import path to GenericModelCodeGenerator subclass.\n"
                 "Works in pair with '-f custom'\n\n"
        )
        parser.add_argument(
            "--code-generator-kwargs",
            metavar="NAME=VALUE",
            nargs="*", type=str,
            help="List of code generator arguments (for __init__ method).\n"
                 "Each argument should be in following format:\n"
                 "    argument_name=value or \"argument_name=value with space\"\n"
                 "Boolean values should be passed in JS style: true | false"
                 "\n\n"
        )

        return parser


def main(version_string=None):
    import sys
    import os

    if os.getenv("TRAVIS", None) or os.getenv("FORCE_COVERAGE", None):
        # Enable coverage if it is Travis-CI or env variable FORCE_COVERAGE set to true
        import coverage

        coverage.process_startup()

    cli = Cli()
    cli.parse_args()
    if not version_string:
        version_string = (
            'r"""\n'
            f'generated by json2python-models v{json_to_models.__version__} at {datetime.now().ctime()}\n'
            f'command: {" ".join(sys.argv)}\n'
            '"""\n'
        )
    print(version_string + cli.run())


def path_split(path: str) -> List[str]:
    """
    Split path into list of components

    :param path: string path
    :return: List of files/patterns
    """
    folders = []
    while True:
        path, folder = os.path.split(path)

        if folder:
            folders.append(folder)
        else:
            if path:
                folders.append(path)
            break
    folders.reverse()
    return folders


def dict_lookup(d: dict, lookup: str) -> Union[dict, list]:
    """
    Extract nested dictionary value from key path.
    If lookup is "-" returns dict as is.

    :param d: Nested dict
    :param lookup: Dot separated lookup path
    :return: Nested value
    """
    while lookup and lookup != "-":
        split = lookup.split('.', 1)
        if len(split) == 1:
            return d[split[0]]
        key, lookup = split
        d = d[key]
    return d


def iter_json_file(path: Path, lookup: str) -> Generator[Union[dict, list], Any, None]:
    """
    Loads given 'path' file, perform lookup and return generator over json list.
    Does not open file until iteration is started.

    :param path: File Path instance
    :param lookup: Dot separated lookup path
    :return:
    """
    with path.open() as f:
        l = json.load(f)
    l = dict_lookup(l, lookup)
    assert isinstance(l, list), f"Dict lookup return {type(l)} but list is expected, check your lookup path"
    yield from l


def safe_json_load(path: Path) -> Union[dict, list]:
    """
    Open file, load json and close it.
    """
    with path.open() as f:
        return json.load(f)


def _process_path(path: str) -> Iterable[Path]:
    """
    Convert path pattern into path iterable.
    If non-pattern path is given return tuple of one element: (path,)

    :param path:
    :return:
    """
    split_path = path_split(path)
    clean_path = list(itertools.takewhile(
        lambda part: "*" not in part and "?" not in part,
        split_path
    ))
    pattern_path = split_path[len(clean_path):]

    if clean_path:
        clean_path = os.path.join(*clean_path)
    else:
        clean_path = "."

    if pattern_path:
        pattern_path = os.path.join(*pattern_path)
    else:
        pattern_path = None

    path = Path(clean_path)
    if pattern_path:
        return path.glob(pattern_path)
    else:
        return path,
