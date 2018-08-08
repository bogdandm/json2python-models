from typing import Optional, List

import attr


@attr.s
class ModelMeta:
    model: type = attr.ib()
    parent: Optional[type] = attr.ib()


class ModelRegistry:
    def __init__(self, k=.7, n=10):
        """

        :param k: Required percent of fields to merge models
        :param n: Required number of fields to merge models
        """
        self.k = k
        self.n = n
        self.registry: List[ModelMeta] = []

    def register(self, model_meta: ModelMeta):
        self.registry.append(model_meta)

    def get_similar(self, model_meta: ModelMeta):
        # noinspection PyDataclass
        fields = attr.fields(model_meta.model)
        field_names = {f.name for f in fields}
        for m in self.registry:
            # noinspection PyDataclass
            existing_fields = attr.fields(m.model)
            existing_field_names = {f.name for f in existing_fields}
            name_intersection = field_names & existing_field_names
            name_intersection_len = len(name_intersection)

            if (
                    name_intersection_len > self.n or
                    name_intersection_len / max(len(field_names), len(existing_field_names)) > self.k
            ):
                yield m
