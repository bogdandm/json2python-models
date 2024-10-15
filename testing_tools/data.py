test_data = [
    {
        "not_required": 1,
        "null_or_bool": None,
        "str_number": "3",
        "child": {
            "x": 1,
            "subitems": [
                {"wrapper": {"x": 1, "subitems": None}},
                {"wrapper": {"x": 3, "subitems": None}},
                1,
                1.0,
            ],
        },
    },
    {
        "not_required": 2,
        "null_or_bool": False,
        "str_number": "6.6",
        "child": {"x": 1},
    },
    {
        "null_or_bool": True,
        "str_number": "8",
        "3d_array": [
            [[0, 1, 2], [3, 4, 5], [6, 7, 8]],
            [[0, 1, 2], [3, 4, 5], [6, 7, 8]],
            [[0, 1, 2], [3, 4, 5], [6, 7, 8]],
        ],
    },
]
