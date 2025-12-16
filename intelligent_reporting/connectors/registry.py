from typing import Dict, Type, Any
from .base_connector import BaseConnector
from ..expection import *


_FILE_REGISTRY: Dict[str, Type[BaseConnector]] = {}
_DB_CONNECTOR: Type[BaseConnector] | None = None

def register_file(exts: list[str]):
    """
    Decorator to register a connector for one or more file extensions
    """
    def decorator(cls: Type[BaseConnector]):
        for ext in exts:
            _FILE_REGISTRY[ext.lower()] = cls
        return cls
    return decorator


def register_db(cls: Type[BaseConnector]):
    """
    Decorator to register the DB connector
    """
    global _DB_CONNECTOR
    _DB_CONNECTOR = cls
    return cls

def register_file_schema_inferer(cls: Type[Any]):
    """
    Decorator to register the flat-file schema inferer
    """
    global _FILE_SCHEMA_INFERER
    _FILE_SCHEMA_INFERER = cls
    return cls


def register_db_schema_inferer(cls: Type[Any]):
    """
    Decorator to register the DB schema inferer
    """
    global _DB_SCHEMA_INFERER
    _DB_SCHEMA_INFERER = cls
    return cls


def get_file_connector(path: str, **options: Any) -> BaseConnector:
    """
    Resolve a file connector based on file extension
    """
    if not _FILE_REGISTRY:
        raise FileConnectorNotFound(
            "No file connectors have been registered"
        )
    for ext, cls in _FILE_REGISTRY.items():
        if path.lower().endswith(ext):
            return cls(path=path, **options)
        
    known_exts = ", ".join(sorted(_FILE_REGISTRY.keys()))
    raise FileConnectorNotFound(
        f"No connector registered for file: {path}\n"
        f"Supported extensions: {known_exts}"
    )


def get_db_connector(db_url: str) -> BaseConnector:
    """
    Resolve the registered DB connector.
    """
    if _DB_CONNECTOR is None:
        raise DBConnectorNotRegistered(
            "No database connector has been registered"
        )
    return _DB_CONNECTOR(db_url=db_url)