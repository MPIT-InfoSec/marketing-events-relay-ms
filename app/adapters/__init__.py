"""Platform adapters for event delivery."""

from app.adapters.base import AdapterResult, BaseAdapter
from app.adapters.factory import get_adapter, register_adapter

__all__ = [
    "BaseAdapter",
    "AdapterResult",
    "get_adapter",
    "register_adapter",
]
