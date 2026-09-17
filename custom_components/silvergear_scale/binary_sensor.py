"""Plataforma binary_sensor para Silvergear Smart Food Scale."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
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
    async_add_entities([SilvergearScaleOverloadSensor(coordinator, entry)])


class SilvergearScaleOverloadSensor(BinarySensorEntity):
    """Sobrecarga (>5kg según la etiqueta).

    Basado en el byte "tipo de mensaje" del paquete (0x00 en vez del 0x01
    habitual), confirmado con una única muestra real de sobrecarga — no
    podemos descartar del todo que ese mismo 0x00 se use también para
    algún otro tipo de error distinto de la sobrecarga.
    """

    _attr_has_entity_name = True
    _attr_name = "Sobrecarga"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(
        self, coordinator: SilvergearScaleCoordinator, entry: ConfigEntry
    ) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.unique_id}_overload"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or "")},
            name="Silvergear Smart Food Scale",
            manufacturer="Karsten International B.V. (Silvergear)",
            model="Smart Food Scale (Art.No 4454)",
        )

    @property
    def is_on(self) -> bool:
        return self._coordinator.overloaded

    @property
    def available(self) -> bool:
        return self._coordinator.client is not None

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._coordinator.add_listener(self._handle_update))

    def _handle_update(self) -> None:
        self.async_write_ha_state()
