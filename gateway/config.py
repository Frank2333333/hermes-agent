"""
Gateway configuration management for the enterprise build.

This branch intentionally supports only internal entrypoints:
- local
- api_server
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from enterprise_policy import filter_platform_mapping
from hermes_cli.config import get_hermes_home
from utils import is_truthy_value

logger = logging.getLogger(__name__)


def _coerce_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "1", "yes", "on"):
            return True
        if lowered in ("false", "0", "no", "off"):
            return False
        return default
    return is_truthy_value(value, default=default)


def _normalize_unauthorized_dm_behavior(value: Any, default: str = "ignore") -> str:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"pair", "ignore"}:
            return normalized
    return default


class Platform(Enum):
    """Known platform identifiers.

    Only LOCAL/API_SERVER are supported in the enterprise build.
    Legacy enum members remain so older runtime code does not crash during
    import, but config loading drops them immediately.
    """

    LOCAL = "local"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    WHATSAPP = "whatsapp"
    SLACK = "slack"
    SIGNAL = "signal"
    MATTERMOST = "mattermost"
    MATRIX = "matrix"
    HOMEASSISTANT = "homeassistant"
    EMAIL = "email"
    SMS = "sms"
    DINGTALK = "dingtalk"
    API_SERVER = "api_server"
    WEBHOOK = "webhook"
    FEISHU = "feishu"
    WECOM = "wecom"
    WECOM_CALLBACK = "wecom_callback"
    WEIXIN = "weixin"
    BLUEBUBBLES = "bluebubbles"
    QQBOT = "qqbot"


SUPPORTED_GATEWAY_PLATFORMS = frozenset({Platform.LOCAL, Platform.API_SERVER})


def _is_supported_platform(platform: Platform) -> bool:
    return platform in SUPPORTED_GATEWAY_PLATFORMS


def _prune_disallowed_platforms(config: "GatewayConfig") -> None:
    config.platforms = {
        platform: platform_config
        for platform, platform_config in filter_platform_mapping(config.platforms).items()
        if _is_supported_platform(platform)
    }


@dataclass
class HomeChannel:
    platform: Platform
    chat_id: str
    name: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform.value,
            "chat_id": self.chat_id,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HomeChannel":
        return cls(
            platform=Platform(data["platform"]),
            chat_id=str(data["chat_id"]),
            name=data.get("name", "Home"),
        )


@dataclass
class SessionResetPolicy:
    mode: str = "both"
    at_hour: int = 4
    idle_minutes: int = 1440
    notify: bool = True
    notify_exclude_platforms: tuple = ("api_server",)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode,
            "at_hour": self.at_hour,
            "idle_minutes": self.idle_minutes,
            "notify": self.notify,
            "notify_exclude_platforms": list(self.notify_exclude_platforms),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionResetPolicy":
        return cls(
            mode=data.get("mode") or "both",
            at_hour=data.get("at_hour") if data.get("at_hour") is not None else 4,
            idle_minutes=(
                data.get("idle_minutes")
                if data.get("idle_minutes") is not None
                else 1440
            ),
            notify=data.get("notify") if data.get("notify") is not None else True,
            notify_exclude_platforms=tuple(
                data.get("notify_exclude_platforms") or ("api_server",)
            ),
        )


@dataclass
class PlatformConfig:
    enabled: bool = False
    token: Optional[str] = None
    api_key: Optional[str] = None
    home_channel: Optional[HomeChannel] = None
    reply_to_mode: str = "first"
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "enabled": self.enabled,
            "reply_to_mode": self.reply_to_mode,
            "extra": self.extra,
        }
        if self.token:
            result["token"] = self.token
        if self.api_key:
            result["api_key"] = self.api_key
        if self.home_channel:
            result["home_channel"] = self.home_channel.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlatformConfig":
        home_channel = None
        if isinstance(data.get("home_channel"), dict):
            try:
                home_channel = HomeChannel.from_dict(data["home_channel"])
            except Exception:
                home_channel = None
        return cls(
            enabled=_coerce_bool(data.get("enabled"), False),
            token=data.get("token"),
            api_key=data.get("api_key"),
            home_channel=home_channel,
            reply_to_mode=data.get("reply_to_mode", "first"),
            extra=data.get("extra", {}) if isinstance(data.get("extra"), dict) else {},
        )


@dataclass
class StreamingConfig:
    enabled: bool = False
    transport: str = "edit"
    edit_interval: float = 1.0
    buffer_threshold: int = 40
    cursor: str = " |"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "transport": self.transport,
            "edit_interval": self.edit_interval,
            "buffer_threshold": self.buffer_threshold,
            "cursor": self.cursor,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StreamingConfig":
        if not isinstance(data, dict):
            return cls()
        return cls(
            enabled=_coerce_bool(data.get("enabled"), False),
            transport=data.get("transport", "edit"),
            edit_interval=float(data.get("edit_interval", 1.0)),
            buffer_threshold=int(data.get("buffer_threshold", 40)),
            cursor=data.get("cursor", " |"),
        )


@dataclass
class GatewayConfig:
    platforms: Dict[Platform, PlatformConfig] = field(default_factory=dict)
    default_reset_policy: SessionResetPolicy = field(default_factory=SessionResetPolicy)
    reset_by_type: Dict[str, SessionResetPolicy] = field(default_factory=dict)
    reset_by_platform: Dict[Platform, SessionResetPolicy] = field(default_factory=dict)
    reset_triggers: List[str] = field(default_factory=lambda: ["/new", "/reset"])
    quick_commands: Dict[str, Any] = field(default_factory=dict)
    sessions_dir: Path = field(default_factory=lambda: get_hermes_home() / "sessions")
    always_log_local: bool = True
    stt_enabled: bool = True
    group_sessions_per_user: bool = True
    thread_sessions_per_user: bool = False
    unauthorized_dm_behavior: str = "ignore"
    streaming: StreamingConfig = field(default_factory=StreamingConfig)
    session_store_max_age_days: int = 90

    def get_connected_platforms(self) -> List[Platform]:
        connected: List[Platform] = []
        for platform, config in self.platforms.items():
            if not _is_supported_platform(platform):
                continue
            if not config.enabled:
                continue
            if platform == Platform.LOCAL:
                connected.append(platform)
                continue
            if platform == Platform.API_SERVER:
                connected.append(platform)
        return connected

    def get_home_channel(self, platform: Platform) -> Optional[HomeChannel]:
        config = self.platforms.get(platform)
        return config.home_channel if config else None

    def get_reset_policy(
        self,
        platform: Optional[Platform] = None,
        session_type: Optional[str] = None,
    ) -> SessionResetPolicy:
        if platform and platform in self.reset_by_platform:
            return self.reset_by_platform[platform]
        if session_type and session_type in self.reset_by_type:
            return self.reset_by_type[session_type]
        return self.default_reset_policy

    def get_unauthorized_dm_behavior(self, platform: Optional[Platform] = None) -> str:
        if platform:
            platform_cfg = self.platforms.get(platform)
            if platform_cfg and "unauthorized_dm_behavior" in platform_cfg.extra:
                return _normalize_unauthorized_dm_behavior(
                    platform_cfg.extra.get("unauthorized_dm_behavior"),
                    self.unauthorized_dm_behavior,
                )
        return self.unauthorized_dm_behavior

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platforms": {p.value: c.to_dict() for p, c in self.platforms.items()},
            "default_reset_policy": self.default_reset_policy.to_dict(),
            "reset_by_type": {k: v.to_dict() for k, v in self.reset_by_type.items()},
            "reset_by_platform": {
                p.value: v.to_dict() for p, v in self.reset_by_platform.items()
            },
            "reset_triggers": self.reset_triggers,
            "quick_commands": self.quick_commands,
            "sessions_dir": str(self.sessions_dir),
            "always_log_local": self.always_log_local,
            "stt_enabled": self.stt_enabled,
            "group_sessions_per_user": self.group_sessions_per_user,
            "thread_sessions_per_user": self.thread_sessions_per_user,
            "unauthorized_dm_behavior": self.unauthorized_dm_behavior,
            "streaming": self.streaming.to_dict(),
            "session_store_max_age_days": self.session_store_max_age_days,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GatewayConfig":
        platforms: Dict[Platform, PlatformConfig] = {}
        for platform_name, platform_data in (data.get("platforms") or {}).items():
            try:
                platform = Platform(platform_name)
            except ValueError:
                continue
            if not _is_supported_platform(platform):
                continue
            if isinstance(platform_data, dict):
                platforms[platform] = PlatformConfig.from_dict(platform_data)

        reset_by_type = {
            type_name: SessionResetPolicy.from_dict(policy_data)
            for type_name, policy_data in (data.get("reset_by_type") or {}).items()
            if isinstance(policy_data, dict)
        }

        reset_by_platform: Dict[Platform, SessionResetPolicy] = {}
        for platform_name, policy_data in (data.get("reset_by_platform") or {}).items():
            try:
                platform = Platform(platform_name)
            except ValueError:
                continue
            if _is_supported_platform(platform) and isinstance(policy_data, dict):
                reset_by_platform[platform] = SessionResetPolicy.from_dict(policy_data)

        sessions_dir = Path(data.get("sessions_dir") or (get_hermes_home() / "sessions"))
        quick_commands = data.get("quick_commands")
        if not isinstance(quick_commands, dict):
            quick_commands = {}

        stt_enabled = data.get("stt_enabled")
        if stt_enabled is None and isinstance(data.get("stt"), dict):
            stt_enabled = data["stt"].get("enabled")

        try:
            session_store_max_age_days = int(data.get("session_store_max_age_days", 90))
            if session_store_max_age_days < 0:
                session_store_max_age_days = 0
        except (TypeError, ValueError):
            session_store_max_age_days = 90

        return cls(
            platforms=platforms,
            default_reset_policy=SessionResetPolicy.from_dict(
                data.get("default_reset_policy") or {}
            ),
            reset_by_type=reset_by_type,
            reset_by_platform=reset_by_platform,
            reset_triggers=data.get("reset_triggers", ["/new", "/reset"]),
            quick_commands=quick_commands,
            sessions_dir=sessions_dir,
            always_log_local=_coerce_bool(data.get("always_log_local"), True),
            stt_enabled=_coerce_bool(stt_enabled, True),
            group_sessions_per_user=_coerce_bool(
                data.get("group_sessions_per_user"),
                True,
            ),
            thread_sessions_per_user=_coerce_bool(
                data.get("thread_sessions_per_user"),
                False,
            ),
            unauthorized_dm_behavior=_normalize_unauthorized_dm_behavior(
                data.get("unauthorized_dm_behavior"),
                "ignore",
            ),
            streaming=StreamingConfig.from_dict(data.get("streaming", {})),
            session_store_max_age_days=session_store_max_age_days,
        )


def _deep_merge(dst: Dict[str, Any], src: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(dst)
    for key, value in src.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _validate_gateway_config(config: GatewayConfig) -> None:
    policy = config.default_reset_policy
    if not (0 <= policy.at_hour <= 23):
        policy.at_hour = 4
    if policy.idle_minutes is None or policy.idle_minutes <= 0:
        policy.idle_minutes = 1440


def _ensure_platform(config: GatewayConfig, platform: Platform) -> PlatformConfig:
    if platform not in config.platforms:
        config.platforms[platform] = PlatformConfig()
    return config.platforms[platform]


def _apply_env_overrides(config: GatewayConfig) -> None:
    if _coerce_bool(os.getenv("API_SERVER_ENABLED"), False):
        api_server = _ensure_platform(config, Platform.API_SERVER)
        api_server.enabled = True
    api_host = os.getenv("API_SERVER_HOST")
    api_port = os.getenv("API_SERVER_PORT")
    if api_host or api_port:
        api_server = _ensure_platform(config, Platform.API_SERVER)
        api_server.enabled = True
        if api_host:
            api_server.extra["host"] = api_host
        if api_port:
            api_server.extra["port"] = api_port


def load_gateway_config() -> GatewayConfig:
    home = get_hermes_home()
    gw_data: Dict[str, Any] = {}

    gateway_json_path = home / "gateway.json"
    if gateway_json_path.exists():
        try:
            with open(gateway_json_path, "r", encoding="utf-8") as f:
                gw_data = json.load(f) or {}
        except Exception as exc:
            logger.warning("Failed to load %s: %s", gateway_json_path, exc)

    try:
        import yaml

        config_yaml_path = home / "config.yaml"
        if config_yaml_path.exists():
            with open(config_yaml_path, encoding="utf-8") as f:
                yaml_cfg = yaml.safe_load(f) or {}

            sr = yaml_cfg.get("session_reset")
            if isinstance(sr, dict):
                gw_data["default_reset_policy"] = sr

            for key in (
                "quick_commands",
                "group_sessions_per_user",
                "thread_sessions_per_user",
                "streaming",
                "reset_triggers",
                "always_log_local",
                "unauthorized_dm_behavior",
                "session_store_max_age_days",
            ):
                if key in yaml_cfg:
                    gw_data[key] = yaml_cfg[key]

            stt_cfg = yaml_cfg.get("stt")
            if isinstance(stt_cfg, dict):
                gw_data["stt"] = stt_cfg

            platforms_data = gw_data.get("platforms", {})
            if not isinstance(platforms_data, dict):
                platforms_data = {}
            yaml_platforms = yaml_cfg.get("platforms")
            if isinstance(yaml_platforms, dict):
                for plat_name in ("api_server",):
                    block = yaml_platforms.get(plat_name)
                    if isinstance(block, dict):
                        platforms_data[plat_name] = _deep_merge(
                            platforms_data.get(plat_name, {}),
                            block,
                        )
            for plat_name in ("api_server",):
                legacy_block = yaml_cfg.get(plat_name)
                if isinstance(legacy_block, dict):
                    platforms_data[plat_name] = _deep_merge(
                        platforms_data.get(plat_name, {}),
                        legacy_block,
                    )
            gw_data["platforms"] = platforms_data
    except Exception as exc:
        logger.warning("Failed to process config.yaml: %s", exc)

    config = GatewayConfig.from_dict(gw_data)
    _apply_env_overrides(config)
    _prune_disallowed_platforms(config)
    _validate_gateway_config(config)
    return config
