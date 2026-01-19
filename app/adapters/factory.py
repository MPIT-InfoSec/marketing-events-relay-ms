"""Adapter factory for platform selection."""

from typing import Type

from app.adapters.base import BaseAdapter

# Registry of platform adapters
_adapters: dict[str, Type[BaseAdapter]] = {}


def register_adapter(platform_code: str):
    """Decorator to register an adapter for a platform code."""
    def decorator(cls: Type[BaseAdapter]):
        _adapters[platform_code] = cls
        cls.platform_code = platform_code
        return cls
    return decorator


def get_adapter(platform_code: str) -> BaseAdapter:
    """
    Get an adapter instance for the given platform code.

    Args:
        platform_code: Platform identifier (e.g., 'meta_capi', 'ga4')

    Returns:
        Adapter instance for the platform

    Raises:
        ValueError: If no adapter registered for the platform
    """
    # Import adapters to ensure registration
    from app.adapters import ga4, meta_capi, pinterest, sgtm, snapchat, tiktok  # noqa

    if platform_code not in _adapters:
        # Fall back to sGTM adapter for unknown platforms
        from app.adapters.sgtm import SgtmAdapter
        return SgtmAdapter()

    adapter_cls = _adapters[platform_code]
    return adapter_cls()


def get_registered_adapters() -> list[str]:
    """Get list of registered platform codes."""
    return list(_adapters.keys())
