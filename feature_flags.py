"""CloudBees Unify feature management integration for the frontend service.

Flags are defined here as code, registered with the Unify server SDK ("Rox"),
and from then on their live values are controlled centrally in CloudBees
Unify (Feature management > Flags) rather than by redeploying the service.

The frontend is server-rendered (Flask + Jinja2, no client-side JS app), so
it uses the same server-side SDK as the backend rather than a client SDK.

Reference: https://docs.cloudbees.com/docs/cloudbees-unify/latest/feature-management/how-to-guides/install-server-side-sdks
"""
import asyncio
import logging
import os

from rox.server.rox_server import Rox
from rox.server.flags.rox_flag import RoxFlag

logger = logging.getLogger(__name__)


class ServerFlags:
    """Feature flags evaluated by the frontend app."""

    def __init__(self):
        # Demo flag proving the CloudBees Unify wiring works end-to-end.
        # Toggle it in the CloudBees Unify UI to show/hide the homepage
        # promo banner without a redeploy.
        self.show_promo_banner = RoxFlag(False)


flags = ServerFlags()

_initialized = False


def init_feature_flags():
    """Register flags and connect to CloudBees Unify. Call once at startup.

    Fails soft: if ROX_SDK_KEY is missing or the connection attempt fails,
    every flag simply keeps the default value it was declared with above
    instead of taking down the app.
    """
    global _initialized
    if _initialized:
        return
    _initialized = True

    Rox.register(flags)

    sdk_key = os.getenv('ROX_SDK_KEY')
    if not sdk_key:
        logger.warning(
            'ROX_SDK_KEY is not set - feature flags will use their default values'
        )
        return

    try:
        asyncio.run(Rox.setup(sdk_key))
        logger.info('Connected to CloudBees Unify feature management')
    except Exception as exc:
        logger.error('Failed to initialize CloudBees Unify feature flags: %s', exc)
