"""Lazy singletons for BPM and FileNet pooled connectors."""

from __future__ import annotations

import logging
from typing import Optional

from config import Settings
from connectors.enterprise_http import EnterpriseRestConnector
from integration_settings_store import get_bpm_init_kwargs, get_filenet_init_kwargs

logger = logging.getLogger(__name__)

bpm_pool: Optional[EnterpriseRestConnector] = None
filenet_pool: Optional[EnterpriseRestConnector] = None


def init_integration_pools(settings: Settings) -> None:
    """Create pooled clients when base URLs are set. Never raises."""
    global bpm_pool, filenet_pool
    bpm_pool = None
    filenet_pool = None

    bpm_kw = get_bpm_init_kwargs(settings)
    if bpm_kw:
        try:
            bpm_pool = EnterpriseRestConnector(**bpm_kw)
            logger.info("IBM BPM connector pool ready (%s)", bpm_kw.get("base_url"))
        except Exception as e:
            logger.warning("IBM BPM connector not initialized: %s", e)

    fn_kw = get_filenet_init_kwargs(settings)
    if fn_kw:
        try:
            filenet_pool = EnterpriseRestConnector(**fn_kw)
            logger.info("FileNet connector pool ready (%s)", fn_kw.get("base_url"))
        except Exception as e:
            logger.warning("FileNet connector not initialized: %s", e)


def shutdown_integration_pools() -> None:
    global bpm_pool, filenet_pool
    if bpm_pool:
        bpm_pool.close()
        bpm_pool = None
    if filenet_pool:
        filenet_pool.close()
        filenet_pool = None
