import argparse
import configparser
import importlib
import itertools
import json
import os.path
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Iterable, List, Tuple, Type, Union

from .models.sqlmodel import SqlModelCodeGenerator

try:
    import ruamel.yaml as yaml
except ImportError:
    try:
        import yaml
    except ImportError:
        yaml = None

from . import __version__ as VERSION
from .dynamic_typing import ModelMeta, register_datetime_classes, registry
from .generator import MetadataGenerator
from .models import ModelsStructureType
from .models.attr import AttrsModelCodeGenerator
from .models.base import GenericModelCodeGenerator, generate_code
from .models.dataclasses import DataclassModelCodeGenerator
from .models.pydantic import PydanticModelCodeGenerator
from .models.structure import compose_models, compose_models_flat
from .registry import (
    ModelCmp, ModelFieldsEquals, ModelFieldsNumberMatch, ModelFieldsPercentMatch, ModelRegistry
)
from .utils import convert_args

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
        "dataclasses": convert_args(DataclassModelCodeGenerator, meta=bool_js_style,
                                    post_init_converters=bool_js_style),
        "pydantic": convert_args(PydanticModelCodeGenerator),
        "sqlmodel": convert_args(SqlModelCodeGenerator),
    }

    def __init__(self):
        self.initialized = False
        self.models_data: Dict[str, Iterable[dict]] = {}  # -m/-l
        self.enable_datetime: bool = False  # --datetime
        self.strings_converters: bool = False  # --strings-converters
        self.max_literals: int = -1  # --max-strings-literals
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
        parser = getattr(FileLoaders, namespace.input_format)
        self.output_file = namespace.output
        self.enable_datetime = namespace.datetime
        disable_unicode_conversion = namespace.disable_unicode_conversion
        self.strings_converters = namespace.strings_converters
        self.max_literals = namespace.max_strings_literals
        merge_policy = [m.split("_") if "_" in m else m for m in namespace.merge]
        structure = namespace.structure
        framework = namespace.framework
        code_generator = namespace.code_generator
        code_generator_kwargs_raw: List[str] = namespace.code_generator_kwargs
        dict_keys_regex: List[str] = namespace.dict_keys_regex
        dict_keys_fields: List[str] = namespace.dict_keys_fields
        preamble: str = namespace.preamble

        for name in namespace.disable_str_serializable_types:
            registry.remove_by_name(name)

        self.setup_models_data(namespace.model or (), namespace.list or (), parser)
        self.validate(merge_policy, framework, code_generator)
        self.set_args(merge_policy, structure, framework, code_generator, code_generator_kwargs_raw,
                      dict_keys_regex, dict_keys_fields, disable_unicode_conversion, preamble)

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
        output = self.version_string + generate_code(
            structure,
            self.model_generator,
            class_generator_kwargs=self.model_generator_kwargs,
            preamble=self.preamble
        )
        if self.output_file:
            with open(self.output_file, "w", encoding="utf-8") as f:
                f.write(output)
            return f"Output is written to {self.output_file}"
        else:
            return output

    @property
    def version_string(self):
        return (
            'r"""\n'
            f'generated by json2python-models v{VERSION} at {datetime.now().ctime()}\n'
            f'command: {" ".join(sys.argv)}\n'
            '"""\n'
        )

    def validate(self, merge_policy, framework, code_generator):
        """
        Validate parsed args

        :param merge_policy: List of merge policies. Each merge policy is either string or string and policy arguments
        :param framework: Framework name (predefined code generator)
        :param code_generator: Code generator import string
        :return:
        """
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

    def setup_models_data(
            self,
            models: Iterable[Union[
                Tuple[str, str],
                Tuple[str, str, str],
            ]],
            models_lists: Iterable[Tuple[str, str, str]],
            parser: 'FileLoaders.T'
    ):
        """
        Initialize lazy loaders for models data
        """
        models_dict: Dict[str, List[dict]] = defaultdict(list)

        models = list(models) + list(models_lists)
        for model_tuple in models:
            if len(model_tuple) == 2:
                model_name, path_raw = model_tuple
                lookup = '-'
            elif len(model_tuple) == 3:
                model_name, lookup, path_raw = model_tuple
            else:
                raise RuntimeError('`--model` argument should contain exactly 2 or 3 strings')

            for real_path in process_path(path_raw):
                iterator = iter_json_file(parser(real_path), lookup)
                models_dict[model_name].extend(iterator)

        self.models_data = models_dict

    def set_args(
            self,
            merge_policy: List[Union[List[str], str]],
            structure: str,
            framework: str,
            code_generator: str,
            code_generator_kwargs_raw: List[str],
            dict_keys_regex: List[str],
            dict_keys_fields: List[str],
            disable_unicode_conversion: bool,
            preamble: str,
    ):
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

        self.model_generator_kwargs = dict(
            post_init_converters=self.strings_converters,
            convert_unicode=not disable_unicode_conversion,
            max_literals=self.max_literals
        )
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
        if preamble:
            preamble = preamble.strip()
        self.preamble = preamble or None
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
            nargs="+", action="append", metavar=("<Model name> [<JSON lookup>] <File path or pattern>", ""),
            help="Model name and its JSON data as path or unix-like path pattern.\n"
                 "'*',  '**' or '?' patterns symbols are supported.\n\n"
                 "JSON data could be array of models or single model\n\n"
                 "If this file contains dict with nested list than you can pass\n"
                 "<JSON lookup>. Deep lookups are supported by dot-separated path.\n"
                 "If no lookup needed pass '-' as <JSON lookup> (default)\n\n"
        )
        parser.add_argument(
            "-i", "--input-format",
            default="json",
            choices=['json', 'yaml', 'ini'],
            help="Input files parser ('PyYaml' is required to parse yaml files)\n\n"
        )
        parser.add_argument(
            "-o", "--output",
            metavar="FILE", default="",
            help="Path to output file\n\n"
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
            default="flat",
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
        parser.add_argument(
            "--max-strings-literals",
            type=int,
            default=GenericModelCodeGenerator.DEFAULT_MAX_LITERALS,
            metavar='NUMBER',
            help="Generate Literal['foo', 'bar'] when field have less than NUMBER string constants as values.\n"
                 f"Pass 0 to disable. By default NUMBER={GenericModelCodeGenerator.DEFAULT_MAX_LITERALS}"
                 f" (some generator classes could override it)\n\n"
        )
        parser.add_argument(
            "--disable-unicode-conversion", "--no-unidecode",
            action="store_true",
            help="Disabling unicode conversion in fields and class names.\n\n"
        )

        default_percent = f"{ModelFieldsPercentMatch.DEFAULT * 100:.0f}"
        default_number = f"{ModelFieldsNumberMatch.DEFAULT:.0f}"
        parser.add_argument(
            "--merge",
            default=["percent", "number"],
            nargs="+",
            help=(
                f"Merge policy settings. Default is 'percent_{default_percent} number_{default_number}' (percent of field match\n"
                "or number of fields match).\n"
                "Possible values are:\n"
                "'percent[_<percent>]' - two models had a certain percentage of matched field names.\n"
                f"                        Default percent is {default_percent}%%. "
                "Custom value could be i.e. 'percent_95'.\n"
                "'number[_<number>]'   - two models had a certain number of matched field names.\n"
                f"                        Default number of fields is {default_number}.\n"
                "'exact'               - two models should have exact same field names to merge.\n\n"
            )
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
        parser.add_argument(
            "--preamble",
            type=str,
            help="Code to insert into the generated file after the imports and before the list of classes\n\n"
        )
        parser.add_argument(
            "--disable-str-serializable-types",
            metavar="TYPE",
            default=[],
            nargs="*", type=str,
            help="List of python types for which StringSerializable should be disabled, i.e:\n"
                 "--disable-str-serializable-types float int\n"
                 "Alternatively you could use the name of StringSerializable subclass itself (i.e. IntString)"
                 "\n\n"
        )
        parser.add_argument(
            "-l", "--list",
            nargs=3, action="append", metavar=("<Model name>", "<JSON lookup>", "<JSON file>"),
            help="DEPRECATED, use --model argument instead"
        )

        return parser


def main():
    import os

    if os.getenv("TRAVIS", None) or os.getenv("FORCE_COVERAGE", None):
        # Enable coverage if it is Travis-CI or env variable FORCE_COVERAGE set to true
        import coverage

        coverage.process_startup()

    cli = Cli()
    cli.parse_args()
    print(cli.run())


class FileLoaders:
    T = Callable[[Path], Union[dict, list]]

    @staticmethod
    def json(path: Path) -> Union[dict, list]:
        with path.open() as fp:
            return json.load(fp)

    @staticmethod
    def yaml(path: Path) -> Union[dict, list]:
        if yaml is None:
            print('Yaml parser is not installed. To parse yaml files PyYaml (or ruamel.yaml) is required.')
            raise ImportError('yaml')
        with path.open() as fp:
            return yaml.safe_load(fp)

    @staticmethod
    def ini(path: Path) -> dict:
        config = configparser.ConfigParser()
        with path.open() as fp:
            config.read_file(fp)
        return {s: dict(config.items(s)) for s in config.sections()}


def dict_lookup(d: Union[dict, list], lookup: str) -> Union[dict, list]:
    """
    Extract nested value from key path.
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


def iter_json_file(data: Union[dict, list], lookup: str) -> Generator[Union[dict, list], Any, None]:
    """
    Perform lookup and return generator over json list.
    Does not open file until iteration is started.

    :param data: JSON data
    :param lookup: Dot separated lookup path
    :return: Generator of the model data
    """
    item = dict_lookup(data, lookup)
    if isinstance(item, list):
        yield from item
    elif isinstance(item, dict):
        yield item
    else:
        raise TypeError(f'dict or list is expected at {lookup if lookup != "-" else "JSON root"}, not {type(item)}')


def process_path(path: str) -> Iterable[Path]:
    """
    Convert path pattern into path iterable.
    If non-pattern path is given return tuple of one element: (path,)
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
