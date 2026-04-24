"""Enterprise-only security policy helpers.

This branch is intentionally locked down for intranet-only deployment:
- only self-hosted/custom model endpoints are allowed
- outbound HTTP targets must be localhost/private or explicitly allowlisted
- public messaging platforms are disabled
"""

from __future__ import annotations

import fnmatch
import ipaddress
import logging
import socket
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterable, Optional
from urllib.parse import urlparse

from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)

_CACHE_TTL_SECONDS = 10.0
_cache_lock = threading.Lock()
_cached_policy: Optional[Dict[str, Any]] = None
_cached_policy_path: Optional[str] = None
_cached_policy_time: float = 0.0

_DEFAULT_ENTERPRISE_POLICY = {
    "enabled": True,
    "network_allowlist": {
        "hosts": [],
        "cidrs": [],
    },
}

ALLOWED_GATEWAY_PLATFORMS = frozenset({"local", "api_server", "webhook", "homeassistant"})
ALLOWED_PROVIDERS = frozenset({"custom"})
_PRIVATE_NETWORKS = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
)


def _get_default_config_path() -> Path:
    return get_hermes_home() / "config.yaml"


def _normalize_host(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    raw = value.strip().lower()
    if not raw:
        return ""
    if "://" in raw:
        parsed = urlparse(raw)
        raw = parsed.hostname or parsed.netloc or raw
    raw = raw.split("/", 1)[0]
    if raw.startswith("[") and "]" in raw:
        raw = raw[1:raw.index("]")]
    elif raw.count(":") <= 1:
        raw = raw.split(":", 1)[0]
    return raw.rstrip(".")


def _load_policy_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    config_path = config_path or _get_default_config_path()
    if not config_path.exists():
        return dict(_DEFAULT_ENTERPRISE_POLICY)

    try:
        import yaml
    except ImportError:
        logger.debug("PyYAML not installed; using default enterprise policy")
        return dict(_DEFAULT_ENTERPRISE_POLICY)

    try:
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except Exception as exc:
        logger.warning("Failed to read enterprise policy from %s: %s", config_path, exc)
        return dict(_DEFAULT_ENTERPRISE_POLICY)

    if not isinstance(config, dict):
        return dict(_DEFAULT_ENTERPRISE_POLICY)

    enterprise = config.get("enterprise") or {}
    if not isinstance(enterprise, dict):
        enterprise = {}

    policy = {
        "enabled": enterprise.get("enabled", True),
        "network_allowlist": {
            "hosts": [],
            "cidrs": [],
        },
    }
    allowlist = enterprise.get("network_allowlist") or {}
    if isinstance(allowlist, dict):
        raw_hosts = allowlist.get("hosts") or []
        if isinstance(raw_hosts, list):
            policy["network_allowlist"]["hosts"] = [
                host for host in (_normalize_host(v) for v in raw_hosts) if host
            ]
        raw_cidrs = allowlist.get("cidrs") or []
        if isinstance(raw_cidrs, list):
            policy["network_allowlist"]["cidrs"] = [
                str(v).strip() for v in raw_cidrs if isinstance(v, str) and str(v).strip()
            ]
    return policy


def load_enterprise_policy(config_path: Optional[Path] = None) -> Dict[str, Any]:
    global _cached_policy, _cached_policy_path, _cached_policy_time

    resolved_path = str(config_path) if config_path else "__default__"
    now = time.monotonic()
    if config_path is None:
        with _cache_lock:
            if (
                _cached_policy is not None
                and _cached_policy_path == resolved_path
                and (now - _cached_policy_time) < _CACHE_TTL_SECONDS
            ):
                return _cached_policy

    policy = _load_policy_config(config_path)
    if config_path is None:
        with _cache_lock:
            _cached_policy = policy
            _cached_policy_path = resolved_path
            _cached_policy_time = now
    return policy


def invalidate_enterprise_policy_cache() -> None:
    global _cached_policy
    with _cache_lock:
        _cached_policy = None


def is_enterprise_enabled(config_path: Optional[Path] = None) -> bool:
    # This branch is intentionally hard-locked to enterprise mode.
    # The config key is retained for explicitness and future migrations,
    # but cannot disable the branch-level restrictions.
    return True


def _iter_allowlisted_cidrs(config_path: Optional[Path] = None) -> Iterable[ipaddress._BaseNetwork]:
    allowlist = load_enterprise_policy(config_path).get("network_allowlist", {})
    for raw in allowlist.get("cidrs", []):
        try:
            yield ipaddress.ip_network(raw, strict=False)
        except ValueError:
            logger.warning("Ignoring invalid enterprise.network_allowlist CIDR: %s", raw)


def _host_matches_rule(host: str, rule: str) -> bool:
    if not host or not rule:
        return False
    if any(ch in rule for ch in "*?[]"):
        return fnmatch.fnmatch(host, rule)
    return host == rule or host.endswith(f".{rule}")


def _is_private_ip(addr: ipaddress._BaseAddress) -> bool:
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or any(addr in network for network in _PRIVATE_NETWORKS)
    )


def _is_ip_allowlisted(addr: ipaddress._BaseAddress, config_path: Optional[Path] = None) -> bool:
    if _is_private_ip(addr):
        return True
    return any(addr in network for network in _iter_allowlisted_cidrs(config_path))


def _resolve_host_ips(host: str) -> list[ipaddress._BaseAddress]:
    resolved: list[ipaddress._BaseAddress] = []
    try:
        addr_info = socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        return resolved
    for _, _, _, _, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            resolved.append(ipaddress.ip_address(ip_str))
        except ValueError:
            continue
    return resolved


def get_enterprise_url_block(
    url: str,
    *,
    config_path: Optional[Path] = None,
) -> Optional[Dict[str, str]]:
    """Return a block payload when enterprise network policy rejects a URL."""
    if not is_enterprise_enabled(config_path):
        return None

    parsed = urlparse(url)
    host = _normalize_host(parsed.hostname or parsed.netloc or url)
    if not host:
        return {
            "host": "",
            "rule": "invalid-target",
            "source": "enterprise.network_allowlist",
            "message": "Blocked: invalid or empty network target.",
        }

    allowlist = load_enterprise_policy(config_path).get("network_allowlist", {})
    for rule in allowlist.get("hosts", []):
        if _host_matches_rule(host, rule):
            return None

    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        addr = None

    if addr is not None:
        if _is_ip_allowlisted(addr, config_path):
            return None
        return {
            "host": host,
            "rule": host,
            "source": "enterprise.network_allowlist",
            "message": (
                "Blocked: outbound target is not localhost, private-network, or in "
                "enterprise.network_allowlist."
            ),
        }

    resolved_ips = _resolve_host_ips(host)
    if resolved_ips and all(_is_ip_allowlisted(ip, config_path) for ip in resolved_ips):
        return None

    return {
        "host": host,
        "rule": host,
        "source": "enterprise.network_allowlist",
        "message": (
            "Blocked: outbound target is not localhost, private-network, or in "
            "enterprise.network_allowlist."
        ),
    }


def ensure_enterprise_url_allowed(
    url: str,
    *,
    config_path: Optional[Path] = None,
    error_cls: type[Exception] = ValueError,
    prefix: str = "",
) -> None:
    blocked = get_enterprise_url_block(url, config_path=config_path)
    if blocked:
        message = blocked["message"]
        if prefix:
            message = f"{prefix}{message}"
        raise error_cls(message)


def is_provider_allowed(provider: str) -> bool:
    normalized = (provider or "").strip().lower()
    return normalized in ALLOWED_PROVIDERS


def validate_provider_or_raise(provider: str, *, error_cls: type[Exception] = ValueError) -> None:
    normalized = (provider or "").strip().lower()
    if normalized in {"", "auto"}:
        return
    if not is_provider_allowed(normalized):
        raise error_cls(
            f"Provider '{normalized}' is disabled in the enterprise build. "
            "Only self-hosted/custom endpoints are allowed."
        )


def is_gateway_platform_allowed(platform_name: str) -> bool:
    return (platform_name or "").strip().lower() in ALLOWED_GATEWAY_PLATFORMS


def filter_platform_mapping(platforms: Dict[Any, Any]) -> Dict[Any, Any]:
    return {
        key: value
        for key, value in (platforms or {}).items()
        if is_gateway_platform_allowed(getattr(key, "value", str(key)))
    }
