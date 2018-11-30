from collections import defaultdict
from typing import Dict, Generic, Iterable, List, Set, Tuple, TypeVar, Union

from ..dynamic_typing import DOptional, ModelMeta, ModelPtr

Index = str
ModelsStructureType = Tuple[List[dict], Dict[ModelMeta, ModelMeta]]

T = TypeVar('T')


class ListEx(list, Generic[T]):
    """
    Extended list with shortcut methods
    """

    def safe_index(self, value: T):
        try:
            return self.index(value)
        except ValueError:
            return None

    def _safe_indexes(self, *values: T):
        return [i for i in map(self.safe_index, values) if i is not None]

    def insert_before(self, value: T, *before: T):
        ix = self._safe_indexes(*before)
        if not ix:
            raise ValueError
        pos = min(ix)
        self.insert(pos, value)
        return pos

    def insert_after(self, value: T, *after: T):
        ix = self._safe_indexes(*after)
        if not ix:
            raise ValueError
        pos = max(ix) + 1
        self.insert(pos, value)
        return pos


class PositionsDict(defaultdict):
    # Dict contains mapping Index -> position, where position is list index to insert nested element of Index
    INC = object()

    def __init__(self, default_factory=int, **kwargs):
        super().__init__(default_factory, **kwargs)

    def update_position(self, key: str, value: Union[object, int]):
        """
        Shift all elements which are placed after updated one

        :param key: Index or "root"
        :param value: Could be position or PositionsDict.INC to perform quick increment (x+=1)
        :return:
        """
        if value is self.INC:
            value = self[key] + 1
        if key in self:
            old_value = self[key]
            delta = value - old_value
        else:
            old_value = value
            delta = 1
        for k, v in self.items():
            if k != key and v >= old_value:
                self[k] += delta
        self[key] = value


def compose_models(models_map: Dict[str, ModelMeta]) -> ModelsStructureType:
    """
    Generate nested sorted models structure for internal usage.

    :return: List of root models data, Map(child model -> root model) for absolute ref generation
    """
    root_models = ListEx()
    root_nested_ix = 0
    structure_hash_table: Dict[Index, dict] = {
        key: {
            "model": model,
            "nested": ListEx(),
            "roots": list(extract_root(model)),  # Indexes of root level models
        } for key, model in models_map.items()
    }
    # TODO: Test path_injections
    path_injections: Dict[ModelMeta, ModelMeta] = {}

    for key, model in models_map.items():
        pointers = list(filter_pointers(model))
        has_root_pointers = len(pointers) != len(model.pointers)
        if not pointers:
            # Root level model
            if not has_root_pointers:
                raise Exception(f'Model {model.name} has no pointers')
            root_models.append(structure_hash_table[key])
        else:
            parents = {ptr.parent.index for ptr in pointers}
            struct = structure_hash_table[key]
            # Model is using by other models
            if has_root_pointers or len(parents) > 1 and len(struct["roots"]) > 1:
                # Model is using by different root models
                try:
                    root_models.insert_before(
                        struct,
                        *(structure_hash_table[parent_key] for parent_key in struct["roots"])
                    )
                except ValueError:
                    root_models.insert(root_nested_ix, struct)
                    root_nested_ix += 1
            elif len(parents) > 1 and len(struct["roots"]) == 1:
                # Model is using by single root model
                parent = structure_hash_table[struct["roots"][0]]
                parent["nested"].insert(0, struct)
                path_injections[struct["model"]] = parent["model"]
            else:
                # Model is using by only one model
                parent = structure_hash_table[next(iter(parents))]
                struct = structure_hash_table[key]
                parent["nested"].append(struct)

    return root_models, path_injections


def compose_models_flat(models_map: Dict[Index, ModelMeta]) -> ModelsStructureType:
    """
    Generate flat sorted (by nesting level, ASC) models structure for internal usage.

    :param models_map: Mapping (model index -> model meta instance).
    :return: List of root models data, Map(child model -> root model) for absolute ref generation
    """
    root_models = ListEx()
    positions: PositionsDict[Index, int] = PositionsDict()
    top_level_models: Set[Index] = set()
    structure_hash_table: Dict[Index, dict] = {
        key: {
            "model": model,
            "nested": ListEx(),
            "roots": list(extract_root(model)),  # Indexes of root level models
        } for key, model in models_map.items()
    }

    for key, model in models_map.items():
        pointers = list(filter_pointers(model))
        has_root_pointers = len(pointers) != len(model.pointers)
        if not pointers:
            # Root level model
            if not has_root_pointers:
                raise Exception(f'Model {model.name} has no pointers')
            root_models.insert(positions["root"], structure_hash_table[key])
            top_level_models.add(key)
            positions.update_position("root", PositionsDict.INC)
        else:
            parents = {ptr.parent.index for ptr in pointers}
            struct = structure_hash_table[key]
            # Model is using by other models
            if has_root_pointers or len(parents) > 1 and len(struct["roots"]) >= 1:
                # Model is using by different root models
                if parents & top_level_models:
                    parents.add("root")
                parents_positions = {positions[parent_key] for parent_key in parents
                                     if parent_key in positions}
                parents_joined = "#".join(sorted(parents))
                if parents_joined in positions:
                    parents_positions.add(positions[parents_joined])
                pos = max(parents_positions) if parents_positions else len(root_models)
                positions.update_position(parents_joined, pos + 1)
            else:
                # Model is using by only one model
                parent = next(iter(parents))
                pos = positions.get(parent, len(root_models))
                positions.update_position(parent, pos + 1)
            positions.update_position(key, pos + 1)
            root_models.insert(pos, struct)

    return root_models, {}


def filter_pointers(model: ModelMeta) -> Iterable[ModelPtr]:
    """
    Return iterator over pointers with not None parent
    """
    return (ptr for ptr in model.pointers if ptr.parent)


def extract_root(model: ModelMeta) -> Set[Index]:
    """
    Return set of indexes of root models that are use given ``model`` directly or through another nested model.
    """
    seen: Set[Index] = set()
    nodes: List[ModelPtr] = list(filter_pointers(model))
    roots: Set[Index] = set()
    while nodes:
        node = nodes.pop()
        seen.add(node.type.index)
        filtered = list(filter_pointers(node.parent))
        nodes.extend(ptr for ptr in filtered if ptr.type.index not in seen)
        if not filtered:
            roots.add(node.parent.index)
    return roots


def sort_fields(model_meta: ModelMeta) -> Tuple[List[str], List[str]]:
    """
    Split fields into required and optional groups

    :return: two list of fields names: required fields, optional fields
    """
    fields = model_meta.type
    required = []
    optional = []
    for key, meta in fields.items():
        if isinstance(meta, DOptional):
            optional.append(key)
        else:
            required.append(key)
    return required, optional


INDENT = " " * 4
OBJECTS_DELIMITER = "\n" * 3  # 2 blank lines


def indent(string: str, lvl: int = 1, indent: str = INDENT) -> str:
    """
    Indent all lines of string by ``indent * lvl``
    """
    return "\n".join(indent * lvl + line for line in string.split("\n"))
