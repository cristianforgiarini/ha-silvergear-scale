"""Config flow para Silvergear Smart Food Scale."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class SilvergearScaleConfigFlow(ConfigFlow, domain=DOMAIN):
    """Gestiona el alta de la báscula, por descubrimiento o de forma manual."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_address: str | None = None
        self._discovered_name: str | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """HA nos llama aquí solo cuando ve el servicio 0xFFB0 anunciado (ver manifest.json)."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._discovered_address = discovery_info.address
        self._discovered_name = discovery_info.name or discovery_info.address
        self.context["title_placeholders"] = {"name": self._discovered_name}
        return await self.async_step_confirm()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovered_name or "Silvergear Smart Food Scale",
                data={},
            )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="confirm",
            description_placeholders={"name": self._discovered_name or ""},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Alta manual por si el descubrimiento automático no dispara (p. ej. proxy pasivo)."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input["address"].strip().upper()
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            self._discovered_address = address
            self._discovered_name = "Silvergear Smart Food Scale"
            return self.async_create_entry(title=self._discovered_name, data={})

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("address"): str}),
            errors=errors,
            description_placeholders={
                "hint": "MAC de la báscula, ej. A8:0B:6B:9D:EF:9F"
            },
        )
