"""Enterprise HTTP connectors with connection pooling (IBM BPM, FileNet-style REST)."""

from .registry import (
    filenet_pool,
    bpm_pool,
    init_integration_pools,
    shutdown_integration_pools,
)

__all__ = [
    "bpm_pool",
    "filenet_pool",
    "init_integration_pools",
    "shutdown_integration_pools",
]
