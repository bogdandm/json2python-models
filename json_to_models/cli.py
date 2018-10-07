import argparse
import itertools
import os.path
from pathlib import Path
from typing import Iterable, List, Tuple

from .registry import ModelFieldsNumberMatch, ModelFieldsPercentMatch

ASCII_ART = """\
|-----------------------------------------------------------|
|  __                   ____                   _      _     |
|  \ \  ___  ___  _ __ |___ \  /\/\   ___   __| | ___| |___ |
|   \ \/ __|/ _ \| '_ \  __) |/    \ / _ \ / _` |/ _ \ / __||
|/\_/ /\__ \ (_) | | | |/ __// /\/\ \ (_) | (_| |  __/ \__ \|
|\___/ |___/\___/|_| |_|_____\/    \/\___/ \__,_|\___|_|___/|
|-----------------------------------------------------------|\
"""


def path_split(path: str) -> List[str]:
    folders = []
    while True:
        path, folder = os.path.split(path)

        if folder != "":
            folders.append(folder)
        else:
            if path != "":
                folders.append(path)

            break

    folders.reverse()
    return folders


class Cli:
    MERGE_CHOICES = {"percent", "number", "equal"}

    def __init__(self):
        self._argparser = None

    def run(self, args: List[str] = None):
        parser = self.argparser
        namespace = parser.parse_args(args)
        models: Tuple[str, Iterable[Path]] = [
            (model_name, itertools.chain(*(self._process_path(p) for p in paths)))
            for model_name, *paths in namespace.model or ()
        ]
        models_list: Tuple[str, Tuple[str, Path]] = [
            (model_name, (lookup, Path(path)))
            for model_name, lookup, path in (namespace.list or ())
        ]
        enable_datetime = namespace.datetime
        merge_policy = [m.split("_") if "_" in m else m for m in namespace.merge]
        structure = namespace.structure
        framework = namespace.framework
        code_generator = namespace.code_generator

        self.validate(models, models_list, merge_policy, framework, code_generator)

    def validate(self, models, models_list, merge_policy, framework, code_generator):
        names = {name for name, _ in models}
        if len(names) != len(models):
            raise ValueError("Model names under -m flag should be unique")

        names = {name for name, _ in models_list}
        if len(names) != len(models_list):
            raise ValueError("Model names under -l flag should be unique")

        for m in merge_policy:
            if isinstance(m, list):
                if m[0] not in self.MERGE_CHOICES:
                    raise ValueError(f"Invalid merge policy '{m[0]}', choices are {self.MERGE_CHOICES}")
                int(m[1])
            elif m not in self.MERGE_CHOICES:
                raise ValueError(f"Invalid merge policy '{m}', choices are {self.MERGE_CHOICES}")
        if framework == 'custom' and code_generator is None:
            raise ValueError("You should specify --code-generator to support custom generator")
        elif framework != 'custom' and code_generator is not None:
            raise ValueError("--code-generator argument has no effect without '--framework custom' argument")

    @property
    def argparser(self) -> argparse.ArgumentParser:
        if self._argparser is None:
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
                     "If no lookup needed pass '-'\n\n"

                     "I.e. for file that contains dict {\"a\": {\"b\": [model_data, ...]}} you should\n"
                     "pass 'a.b' as <JSON key>.\n\n"
            )
            parser.add_argument(
                "--datetime",
                action="store_true",
                help="Enable datetime/date/time strings parsing.\n"
                     "Warn.: This can lead to 6-7 times slowdown on large datasets.\n"
                     "       Be sure that you really need this option.\n\n"
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
                     "'number[_<number>]' - two models had a certain number of matched field names.\n"
                     f"                      Default number of fields is {default_number}.\n"
                     "'equal' - two models should have exact same field names to merge.\n\n"
            )
            parser.add_argument(
                "-s", "--structure",
                default="nested",
                choices=["nested", "flat"],
                help="Models composition style. By default nested models become nested Python classes.\n\n"
            )
            parser.add_argument(
                "-f", "--framework",
                default="base",
                choices=["base", "attrs", "dataclasses", "custom"],
                help="Model framework for which python code is generated.\n"
                     "'base' (default) mean no framework so code will be generated without any decorators\n"
                     "and additional meta-data.\n"
                     "If you pass 'custom' you should specify --code-generator argument\n\n"
            )
            parser.add_argument(
                "--code-generator",
                help="Absolute import path to GenericModelCodeGenerator subclass.\n"
                     "Works in pair with '-f custom'\n\n"
            )

            self._argparser = parser
        return self._argparser

    def _process_path(self, path: str) -> Iterable[Path]:
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
