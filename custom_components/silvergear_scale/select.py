"""Plataforma select para elegir la unidad de la báscula desde HA."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import SilvergearScaleCoordinator
from .const import DOMAIN, NOTIFY_UNIT_MAP, UNIT_WRITE_COMMANDS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SilvergearScaleCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([SilvergearScaleUnitSelect(coordinator, entry)])


class SilvergearScaleUnitSelect(SelectEntity):
    """Cambia la unidad mostrada en la báscula (g / ml / ml(m)).

    OJO: solo hemos capturado y confirmado estas 3 unidades (faltan oz y
    lb-oz). Además "ml" no mide volumen de verdad: la báscula asume
    densidad 1 y reetiqueta el mismo valor crudo en gramos, así que el
    sensor de peso principal se queda siempre en gramos independientemente
    de lo que elijas aquí — esto solo cambia lo que muestra la pantalla
    física de la báscula.
    """

    _attr_has_entity_name = True
    _attr_name = "Unidad mostrada"
    _attr_options = list(UNIT_WRITE_COMMANDS.keys())
    _attr_icon = "mdi:scale-balance"

    def __init__(
        self, coordinator: SilvergearScaleCoordinator, entry: ConfigEntry
    ) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.unique_id}_unit"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id or "")},
            name="Silvergear Smart Food Scale",
            manufacturer="Karsten International B.V. (Silvergear)",
            model="Smart Food Scale (Art.No 4454)",
        )

    @property
    def current_option(self) -> str | None:
        raw = self._coordinator.unit_raw
        if raw is None:
            return None
        return NOTIFY_UNIT_MAP.get(raw)

    @property
    def available(self) -> bool:
        return self._coordinator.client is not None

    async def async_select_option(self, option: str) -> None:
        await self._coordinator.async_set_unit(option)

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._coordinator.add_listener(self._handle_update))

    def _handle_update(self) -> None:
        self.async_write_ha_state()
