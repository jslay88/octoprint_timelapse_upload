from importlib import import_module
from inspect import getmembers, isclass
from pkgutil import iter_modules

from . import clients
from .clients.base import BaseClient


def discover_clients() -> dict:
    _clients = {}
    for _, name, is_pkg in iter_modules(clients.__path__, clients.__name__ + "."):
        base_name = name.split('.')[-1]
        if base_name.startswith("_") or base_name == "base":
            continue
        for client_name, client_class in filter_client_classes(name):
            _clients[client_name] = client_class
    return _clients


def filter_client_classes(name) -> tuple[str, BaseClient]:
    print(f'Filter Classes for {name}')
    _module = import_module(name)
    for k, v in getmembers(_module):
        if k.startswith('_'):
            continue
        if isclass(v) and v is not BaseClient and issubclass(v, BaseClient):
            print(f"Found Client: {k}")
            yield k, v
