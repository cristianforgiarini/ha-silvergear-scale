"""Plataforma sensor para Silvergear Smart Food Scale."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SilvergearScaleCoordinator
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SilvergearScaleCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SilvergearScaleWeightSensor(coordinator, entry)])


class SilvergearScaleWeightSensor(SensorEntity):
    """Peso instantáneo reportado por la báscula, en gramos."""

    _attr_has_entity_name = True
    _attr_name = "Peso"
    _attr_device_class = SensorDeviceClass.WEIGHT
    _attr_native_unit_of_measurement = UnitOfMass.GRAMS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(
        self, coordinator: SilvergearScaleCoordinator, entry: ConfigEntry
    ) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.unique_id}_weight"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or "")},
            name="Silvergear Smart Food Scale",
            manufacturer="Karsten International B.V. (Silvergear)",
            model="Smart Food Scale (Art.No 4454)",
        )

    @property
    def native_value(self) -> float | None:
        return self._coordinator.weight_grams

    @property
    def available(self) -> bool:
        return self._coordinator.weight_grams is not None

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._coordinator.add_listener(self._handle_update))

    def _handle_update(self) -> None:
        self.async_write_ha_state()
