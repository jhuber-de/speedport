"""Config flow for Speedport integration."""

from __future__ import annotations

import logging
from typing import Any

from speedport import Speedport
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("host", default="speedport.ip"): str,
        vol.Required("password"): str,
        vol.Optional("https", default=False): bool,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""

    speedport = await Speedport(
        host=data["host"], password=data["password"], https=data["https"]
    ).create()

    if not await speedport.login(data["password"]):
        raise InvalidAuth

    await speedport.update_status()

    return {
        "title": "Speedport",
        "hybrid_detected": speedport.get("use_lte") == "1",
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Speedport."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._user_input: dict[str, Any] = {}
        self._title: str = ""
        self._hybrid_detected: bool = True

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            self._user_input = user_input
            self._title = info["title"]
            self._hybrid_detected = info["hybrid_detected"]
            return await self.async_step_hybrid()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_hybrid(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ask whether hybrid (4G/5G) sensors should be created."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._title,
                data=self._user_input,
                options={"show_hybrid_sensors": user_input["show_hybrid_sensors"]},
            )

        return self.async_show_form(
            step_id="hybrid",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "show_hybrid_sensors", default=self._hybrid_detected
                    ): bool
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "pause_time",
                        default=self.config_entry.options.get("pause_time", 5),
                    ): int,
                    vol.Required(
                        "show_hybrid_sensors",
                        default=self.config_entry.options.get(
                            "show_hybrid_sensors", True
                        ),
                    ): bool,
                }
            ),
        )
