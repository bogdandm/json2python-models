from typing import Dict, Generic, Iterable, List, Set, Tuple, TypeVar

from ..dynamic_typing import DOptional, ModelMeta, ModelPtr

Index = str
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

    def insert_after(self, value: T, *after: T):
        ix = self._safe_indexes(*after)
        if not ix:
            raise ValueError
        pos = max(ix)
        self.insert(pos + 1, value)


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


ModelsStructureType = Tuple[List[dict], Dict[ModelMeta, ModelMeta]]


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
