from typing import Union, TypeVar, Dict, Any
from pathlib import Path


class ConfigBase:
    pass


def load_from_file(file: Union[Path, str], clazz) -> ConfigBase:
    import os
    if not os.path.exists(file):
        return clazz()
    with open(file, "rb") as py_file:
        code_obj = compile(py_file.read(), file, "exec")
        config_vars: Dict[str, Any] = {}
        exec(code_obj, config_vars)
        instance = clazz()
        for key, value in config_vars.items():
            if not key.startswith("__") and hasattr(instance, key):
                setattr(instance, key, value)
        return instance
