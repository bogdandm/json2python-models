from enum import Enum
from typing import Dict, List, Tuple

from ..dynamic_typing import ModelMeta

Index = str
ModelsStructureType = Tuple[List[dict], Dict[ModelMeta, ModelMeta]]

INDENT = " " * 4
OBJECTS_DELIMITER = "\n" * 3  # 2 blank lines


class ClassType(Enum):
    Dataclass = "dataclass"
    Attrs = "attrs"
