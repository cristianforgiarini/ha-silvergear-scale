"""Integración Silvergear Smart Food Scale (Art.No 4454)."""
from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import timedelta

from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    CHAR_NOTIFY_UUID,
    CHAR_WRITE_UUID,
    DOMAIN,
    PACKET_HEADER,
    UNIT_WRITE_COMMANDS,
    WEIGHT_LENGTH,
    WEIGHT_OFFSET,
)

# Reintento de respaldo: no depende de que llegue un anuncio BLE justo a
# tiempo, por si el callback de descubrimiento o el de desconexión de Bleak
# se retrasan o no llegan a disparar.
_RECONNECT_INTERVAL = timedelta(seconds=30)

PLATFORMS = ["sensor", "select"]
_LOGGER = logging.getLogger(__name__)


class SilvergearScaleCoordinator:
    """Mantiene la conexión GATT activa y el último peso conocido.

    La báscula NO mete el peso en el paquete de advertising: hay que
    mantener una conexión GATT abierta y escuchar notificaciones en
    CHAR_NOTIFY_UUID. Por eso esto no es un sensor pasivo tipo Xiaomi BLE,
    sino un cliente BLE activo (igual que hace la app Nutridays).
    """

    def __init__(self, hass: HomeAssistant, address: str) -> None:
        self.hass = hass
        self.address = address
        self.client: BleakClientWithServiceCache | None = None
        self.weight_grams: float | None = None
        self.unit_raw: int | None = None
        self._listeners: list[Callable[[], None]] = []

    def add_listener(self, callback: Callable[[], None]) -> Callable[[], None]:
        self._listeners.append(callback)

        def remove() -> None:
            self._listeners.remove(callback)

        return remove

    def _notify_listeners(self) -> None:
        for callback in self._listeners:
            callback()

    def _handle_notification(self, _sender, data: bytearray) -> None:
        if len(data) < WEIGHT_OFFSET + WEIGHT_LENGTH or bytes(data[:3]) != PACKET_HEADER:
            _LOGGER.debug("Paquete inesperado de %s: %s", self.address, data.hex())
            return

        self.unit_raw = data[3]
        raw_weight_mg = int.from_bytes(
            data[WEIGHT_OFFSET : WEIGHT_OFFSET + WEIGHT_LENGTH], byteorder="big"
        )
        self.weight_grams = raw_weight_mg / 1000
        self._notify_listeners()

    def _handle_disconnect(self, _client: BleakClientWithServiceCache) -> None:
        _LOGGER.debug("Báscula %s desconectada", self.address)
        self.client = None

    async def async_connect(self) -> bool:
        if self.client is not None and self.client.is_connected:
            return True

        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if ble_device is None:
            _LOGGER.debug(
                "Báscula %s no visible ahora mismo; se reintentará al detectarla",
                self.address,
            )
            return False

        try:
            client = await establish_connection(
                BleakClientWithServiceCache,
                ble_device,
                self.address,
                disconnected_callback=self._handle_disconnect,
            )
            await client.start_notify(CHAR_NOTIFY_UUID, self._handle_notification)
        except Exception as err:  # noqa: BLE001 - queremos capturar cualquier fallo de bleak
            _LOGGER.warning("No se pudo conectar con la báscula %s: %s", self.address, err)
            return False

        self.client = client
        _LOGGER.debug("Conectado y suscrito a notificaciones de %s", self.address)
        return True

    async def async_set_unit(self, unit: str) -> bool:
        """Manda el comando de cambio de unidad capturado por HCI snoop."""
        if unit not in UNIT_WRITE_COMMANDS:
            _LOGGER.warning("Unidad '%s' no soportada; no se manda nada", unit)
            return False
        if self.client is None or not self.client.is_connected:
            _LOGGER.warning(
                "No se puede cambiar de unidad: báscula %s no conectada", self.address
            )
            return False
        try:
            await self.client.write_gatt_char(CHAR_WRITE_UUID, UNIT_WRITE_COMMANDS[unit])
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "Fallo al mandar el comando de unidad '%s' a %s: %s", unit, self.address, err
            )
            return False
        return True

    async def async_disconnect(self) -> None:
        if self.client is not None and self.client.is_connected:
            try:
                await self.client.stop_notify(CHAR_NOTIFY_UUID)
            except Exception:  # noqa: BLE001
                pass
            await self.client.disconnect()
        self.client = None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    address = entry.unique_id
    assert address is not None

    coordinator = SilvergearScaleCoordinator(hass, address)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # No bloqueamos aquí con "await": si la báscula está apagada,
    # async_connect() puede tardar bastante (9 reintentos con backoff en
    # bleak_retry_connector), y eso retrasaría el arranque de TODA la
    # instancia de HA, no solo esta integración. Lo lanzamos en segundo
    # plano; el sensor sale como "no disponible" hasta que conecte.
    hass.async_create_task(
        coordinator.async_connect(), f"{DOMAIN}_initial_connect_{address}"
    )

    @callback
    def _on_bluetooth_update(_service_info, _change) -> None:
        # OJO: este callback lo invoca HA de forma síncrona. Si lo
        # declaramos como "async def" nunca se ejecuta de verdad (solo se
        # crea la corutina y se descarta) — por eso antes no reconectaba.
        if coordinator.client is None:
            hass.async_create_task(coordinator.async_connect())

    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            _on_bluetooth_update,
            {"address": address},
            bluetooth.BluetoothScanningMode.PASSIVE,
        )
    )

    @callback
    def _on_unavailable(_service_info) -> None:
        _LOGGER.debug("Báscula %s ya no se ve (unavailable)", address)
        coordinator.client = None
        coordinator._notify_listeners()  # refresca "available" en la entidad

    entry.async_on_unload(
        bluetooth.async_track_unavailable(hass, _on_unavailable, address, connectable=True)
    )

    async def _periodic_reconnect(_now) -> None:
        if coordinator.client is None:
            await coordinator.async_connect()

    entry.async_on_unload(
        async_track_time_interval(hass, _periodic_reconnect, _RECONNECT_INTERVAL)
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator: SilvergearScaleCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
    await coordinator.async_disconnect()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
