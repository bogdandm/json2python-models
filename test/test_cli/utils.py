import importlib.util


def create_module(name: str):
    """
    An alternative approach to `imp.new_module` function, now that imp is
    removed as of py3.12.
    Args:
        name: str

    Returns:
        module
    """
    spec = importlib.util.spec_from_loader(name, loader=None)
    module = importlib.util.module_from_spec(spec=spec)

    return module
