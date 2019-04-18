from collections import defaultdict
from itertools import chain, combinations
from typing import Dict, Iterable, List, Set, Tuple

from ordered_set import OrderedSet

from .dynamic_typing import BaseType, MetaData, ModelMeta, ModelPtr
from .utils import Index, distinct_words


class ModelCmp:
    """
    Generic model comparator
    """

    def cmp(self, fields_a: set, fields_b: set) -> bool:
        raise NotImplementedError()


class ModelFieldsEquals(ModelCmp):
    def cmp(self, fields_a: set, fields_b: set) -> bool:
        return fields_a == fields_b


class ModelFieldsPercentMatch(ModelCmp):
    DEFAULT = .7

    def __init__(self, percent_fields: float = DEFAULT):
        self.percent_fields = percent_fields

    def cmp(self, fields_a: set, fields_b: set) -> bool:
        return len(fields_a & fields_b) / len(fields_a | fields_b) >= self.percent_fields


class ModelFieldsNumberMatch(ModelCmp):
    DEFAULT = 10

    def __init__(self, number_fields: int = DEFAULT):
        self.number_fields = number_fields

    def cmp(self, fields_a: set, fields_b: set) -> bool:
        return len(fields_a & fields_b) >= self.number_fields


class ModelRegistry:
    DEFAULT_MODELS_CMP = (ModelFieldsPercentMatch(), ModelFieldsNumberMatch())

    def __init__(self, *models_cmp: ModelCmp):
        """
        :param models_cmp: list of model comparators. If you want merge only equals models pass ModelFieldsEquals()
        """
        self._models_cmp = models_cmp or self.DEFAULT_MODELS_CMP
        self._registry: Dict[str, ModelMeta] = {}
        self._index = Index()

    @property
    def models(self):
        return self._registry.values()

    @property
    def models_map(self):
        return self._registry

    def process_meta_data(
            self, meta: MetaData,
            model_name: str = None,
            parent: MetaData = None,
            parent_model: Tuple[ModelMeta, str] = (None, None),
            replace_kwargs=None
    ) -> ModelPtr:
        """
        Convert metadata (dict) to model and return a pointer to this model

        :param meta: Dict[str, MetaData] - usually result of MetadataGenerator.generate method call
        :param model_name: Raw model name. Will be set as is.
            It is recommended to set it for root level models because names can not be generated for such models
        :param parent: System attribute for recursive call
        :param parent_model: Pair of (ModelMeta, field name). System attribute for recursive call
        :param replace_kwargs: System attribute for recursive call
        :return:
        """
        replace_kwargs = replace_kwargs or {}
        ptr = None

        if isinstance(meta, dict):
            # Register model
            model_meta = self._register(meta)
            ptr = ModelPtr(model_meta, parent=parent_model[0], parent_field_name=parent_model[1])
            if parent:
                parent.replace(ptr, **replace_kwargs)

            # Process nested data
            for key, value in meta.items():
                nested_ptr = self.process_meta_data(value, parent_model=(model_meta, key))
                if nested_ptr:
                    meta[key] = nested_ptr

        elif isinstance(meta, BaseType):
            # Process other non-atomic types
            try:
                meta_iter = iter(meta)
            except TypeError:
                pass
            else:
                for i, nested_meta in enumerate(meta_iter):
                    self.process_meta_data(
                        nested_meta,
                        parent=meta,
                        parent_model=parent_model,
                        replace_kwargs={'parent': meta, 'index': i}
                    )

        if model_name is not None:
            ptr.type.set_raw_name(model_name)
        return ptr

    def _register(self, meta: MetaData):
        model_meta = ModelMeta(meta, self._index()) if not isinstance(meta, ModelMeta) else meta
        self._registry[model_meta.index] = model_meta
        return model_meta

    def _unregister(self, model_meta: ModelMeta):
        del self._registry[model_meta.index]

    def _models_cmp_fn(self, model_a: ModelMeta, model_b: ModelMeta) -> bool:
        """
        Return True if ANY of comparators decided to merge pair of models
        """
        fields_a = set(model_a.type.keys())
        fields_b = set(model_b.type.keys())
        return any(cmp.cmp(fields_a, fields_b) for cmp in self._models_cmp)

    def merge_models(self, generator, strict=False) -> List[Tuple[ModelMeta, Set[ModelMeta]]]:
        """
        Optimize whole models registry by merging same or similar models (uses given models comparators)

        :param generator: Generator instance that will be used to metadata merging and optimization
        :param strict: if True ALL models in merge group should meet the conditions
            else groups will form from pairs of models as is.
        :return: pairs of (new model, set of old models)
        """
        # TODO: Implement strict mode
        models2merge: Dict[ModelMeta, Set[ModelMeta]] = defaultdict(set)
        for model_a, model_b in combinations(self.models, 2):
            if self._models_cmp_fn(model_a, model_b):
                models2merge[model_a].add(model_b)
                models2merge[model_b].add(model_a)

        # Groups of models to merge
        groups: Iterable[Set[ModelMeta]] = [{model, *models} for model, models in models2merge.items()]
        # Make groups non-overlapping.
        # This is not optimal algorithm but it works and we probably will not have thousands of models here.
        flag = True
        while flag:
            flag = False
            new_groups: OrderedSet[Set[ModelMeta]] = OrderedSet()
            for gr1, gr2 in combinations(groups, 2):
                if gr1 & gr2:
                    old_len = len(new_groups)
                    new_groups.add(frozenset(gr1 | gr2))
                    added = old_len < len(new_groups)
                    flag = flag or added
            if flag:
                groups = new_groups

        replaces = []
        replaces_ids = set()
        for group in groups:
            model_meta = self._merge(generator, *group)
            generator.optimize_type(model_meta)
            replaces_ids.add(model_meta.index)
            replaces.append((model_meta, group))

        for model_meta in self.models:
            if model_meta.index not in replaces_ids:
                generator.optimize_type(model_meta)
        return replaces

    def _merge(self, generator, *models: ModelMeta):
        """
        Merge models by generator.merge_field_sets method.
        Also ensure that the new model will have all metadata from old ones
        """
        original_fields = list(chain(model.original_fields for model in models))
        originals_names = []
        for model in models:
            if not model.is_name_generated and model.name:
                originals_names.append(model.name)
        originals_names = distinct_words(*originals_names)

        metadata = generator.merge_field_sets([model.type for model in models])
        model_meta = ModelMeta(metadata, self._index(), original_fields)
        if originals_names:
            model_meta.set_raw_name(ModelMeta.name_joiner(*sorted(originals_names)))
        for model in models:
            self._unregister(model)
            for ptr in tuple(model.pointers):
                ptr.replace(model_meta)
            for ptr in tuple(model.child_pointers):
                ptr.replace_parent(model_meta)
        self._register(model_meta)

        return model_meta

    def fix_name_duplicates(self):
        """
        Add model's index to all duplicate names
        """
        counter = defaultdict(int)
        for model in self.models:
            counter[model.name or model.index] += 1
            if counter[model.name] > 1:
                model.set_raw_name(model.name_joiner(model.name, model.index), generated=True)

    def generate_names(self):
        for model in self.models:
            if model.is_name_generated is None:
                model.generate_name()
            if model.name is None:
                model.set_raw_name("Unknown_" + model.index, True)
        self.fix_name_duplicates()
