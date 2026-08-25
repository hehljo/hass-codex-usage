"""Sensors for Codex Pulse."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import CodexUsageConfigEntry, CodexUsageCoordinator
from .const import CONF_ACCOUNT_EMAIL, CONF_PLAN_TYPE, DOMAIN, SENSOR_DEFINITIONS


async def async_setup_entry(
    hass,
    entry: CodexUsageConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create static sensors and discover every current or future usage window."""
    coordinator = entry.runtime_data
    async_add_entities(
        CodexUsageSensor(coordinator, entry, key, name, unit, icon, device_class)
        for key, name, unit, icon, device_class in SENSOR_DEFINITIONS
    )
    known_limit_keys: set[str] = set()

    def sync_limit_entities() -> None:
        limits = (coordinator.data or {}).get("limits", {})
        new_entities = [
            CodexUsageLimitSensor(coordinator, entry, key, details["label"])
            for key, details in limits.items()
            if key not in known_limit_keys
        ]
        if new_entities:
            known_limit_keys.update(entity.limit_key for entity in new_entities)
            async_add_entities(new_entities)

    sync_limit_entities()
    entry.async_on_unload(coordinator.async_add_listener(sync_limit_entities))


class _CodexPulseEntity(CoordinatorEntity[CodexUsageCoordinator]):
    """Shared device definition for every Codex Pulse entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CodexUsageCoordinator, entry: CodexUsageConfigEntry) -> None:
        super().__init__(coordinator)
        account = entry.data.get(CONF_ACCOUNT_EMAIL)
        plan = entry.data.get(CONF_PLAN_TYPE)
        title = "Codex Pulse"
        if account:
            title = f"{title} · {account}"
        if plan:
            title = f"{title} ({plan})"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=title,
            entry_type=DeviceEntryType.SERVICE,
        )


class CodexUsageSensor(_CodexPulseEntity, SensorEntity):
    """One stable metric from Codex's current usage snapshot."""

    def __init__(
        self,
        coordinator: CodexUsageCoordinator,
        entry: CodexUsageConfigEntry,
        key: str,
        name: str,
        unit: str | None,
        icon: str,
        device_class: str | None,
    ) -> None:
        super().__init__(coordinator, entry)
        self._key = key
        self._is_timestamp = device_class == "timestamp"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_icon = icon
        self._attr_native_unit_of_measurement = unit
        if self._is_timestamp:
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
        elif unit is not None and key != "api_error":
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def available(self) -> bool:
        if self._key == "api_error":
            return True
        return super().available and self._key in (self.coordinator.data or {})

    @property
    def native_value(self) -> Any:
        if self._key == "api_error":
            return 0 if self.coordinator.last_update_success else 1
        value = (self.coordinator.data or {}).get(self._key)
        if self._is_timestamp and isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return value


class CodexUsageLimitSensor(_CodexPulseEntity, SensorEntity):
    """A discovered usage window, including new model-specific limits."""

    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:chart-donut"

    def __init__(
        self,
        coordinator: CodexUsageCoordinator,
        entry: CodexUsageConfigEntry,
        key: str,
        label: str,
    ) -> None:
        super().__init__(coordinator, entry)
        self.limit_key = key
        self._attr_unique_id = f"{entry.entry_id}_limit_{key}"
        self._attr_name = label

    def _details(self) -> dict[str, Any] | None:
        return (self.coordinator.data or {}).get("limits", {}).get(self.limit_key)

    @property
    def available(self) -> bool:
        return super().available and self._details() is not None

    @property
    def native_value(self) -> Any:
        details = self._details()
        return details.get("used_percent") if details else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        details = self._details()
        if details is None:
            return None
        return {
            "remaining_percent": details.get("remaining_percent"),
            "window_minutes": details.get("window_minutes"),
            "resets_at": details.get("resets_at"),
            "limit_id": details.get("limit_id"),
            "window": details.get("window"),
        }
