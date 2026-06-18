"""Config flow per Termostato Intelligente FV."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_BATTERY_SENSOR,
    CONF_BELOW_OFFSET,
    CONF_CLIMATE_ENTITY,
    CONF_CONSUMPTION_SENSOR,
    CONF_EXTREME_DELTA,
    CONF_EXTREME_OFFSET,
    CONF_FV_END_TIME,
    CONF_FV_MARGIN_W,
    CONF_FV_SENSOR,
    CONF_FV_START_TIME,
    CONF_HOT_OFFSET,
    CONF_NAME,
    CONF_NOTIFY_CHAT_IDS,
    CONF_NOTIFY_MESSAGE,
    CONF_NOTIFY_TARGETS,
    CONF_PRESENCE_BOOST_ENABLED,
    CONF_PRESENCE_BOOST_MIN,
    CONF_PRESENCE_BOOST_OFFSET,
    CONF_PRESENCE_SENSOR,
    CONF_RANGE_OFFSET,
    CONF_SOC_MIN,
    CONF_TARGET_TEMP_DEFAULT,
    CONF_TEMP_DELTA,
    CONF_TEMP_SENSOR,
    CONF_TTS_ENGINE,
    CONF_TTS_MESSAGE_OPEN,
    CONF_TTS_PLAYERS,
    CONF_TURN_ON_OFFSET,
    CONF_UPDATE_INTERVAL_MIN,
    CONF_WINDOW_DELAY_MIN,
    CONF_WINDOW_SENSOR,
    DEFAULT_FV_END_TIME,
    DEFAULT_EXTREME_DELTA,
    DEFAULT_EXTREME_OFFSET,
    DEFAULT_FV_MARGIN_W,
    DEFAULT_FV_START_TIME,
    DEFAULT_BELOW_OFFSET,
    DEFAULT_HOT_OFFSET,
    DEFAULT_NAME,
    DEFAULT_NOTIFY_MESSAGE,
    DEFAULT_PRESENCE_BOOST_ENABLED,
    DEFAULT_PRESENCE_BOOST_MIN,
    DEFAULT_PRESENCE_BOOST_OFFSET,
    DEFAULT_RANGE_OFFSET,
    DEFAULT_SOC_MIN,
    DEFAULT_TARGET_TEMP,
    DEFAULT_TEMP_DELTA,
    DEFAULT_TTS_MESSAGE_OPEN,
    DEFAULT_TURN_ON_OFFSET,
    DEFAULT_UPDATE_INTERVAL_MIN,
    DEFAULT_WINDOW_DELAY_MIN,
    DOMAIN,
)


def _f(schema_cls, key: str, defaults: dict, fallback: Any = None):
    """Costruisce vol.Required/vol.Optional usando un default 'intelligente'.

    Se il valore esiste già nei defaults lo riusa (utile per precompilare i
    form nell'options flow), altrimenti usa il fallback statico se fornito.
    """
    if key in defaults and defaults[key] not in (None, "", []):
        return schema_cls(key, default=defaults[key])
    if fallback is not None:
        return schema_cls(key, default=fallback)
    return schema_cls(key)


def _schema_user(defaults: dict) -> vol.Schema:
    return vol.Schema(
        {
            _f(vol.Required, CONF_NAME, defaults, DEFAULT_NAME): selector.TextSelector(),
            _f(vol.Required, CONF_CLIMATE_ENTITY, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="climate")
            ),
            _f(vol.Required, CONF_TEMP_SENSOR, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            _f(vol.Required, CONF_WINDOW_SENSOR, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            ),
            _f(vol.Optional, CONF_PRESENCE_SENSOR, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="binary_sensor")
            ),
        }
    )


def _schema_energia(defaults: dict) -> vol.Schema:
    return vol.Schema(
        {
            _f(vol.Optional, CONF_FV_SENSOR, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            _f(vol.Optional, CONF_CONSUMPTION_SENSOR, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            _f(vol.Optional, CONF_BATTERY_SENSOR, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            ),
            _f(
                vol.Optional, CONF_FV_MARGIN_W, defaults, DEFAULT_FV_MARGIN_W
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=5000, step=50, unit_of_measurement="W", mode="box"
                )
            ),
            _f(vol.Optional, CONF_SOC_MIN, defaults, DEFAULT_SOC_MIN): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=100, step=1, unit_of_measurement="%", mode="box"
                )
            ),
            _f(
                vol.Optional, CONF_FV_START_TIME, defaults, DEFAULT_FV_START_TIME
            ): selector.TimeSelector(),
            _f(
                vol.Optional, CONF_FV_END_TIME, defaults, DEFAULT_FV_END_TIME
            ): selector.TimeSelector(),
        }
    )


def _schema_soglie(defaults: dict) -> vol.Schema:
    return vol.Schema(
        {
            _f(
                vol.Optional, CONF_TARGET_TEMP_DEFAULT, defaults, DEFAULT_TARGET_TEMP
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=16, max=30, step=0.5, unit_of_measurement="°C", mode="box"
                )
            ),
            _f(
                vol.Optional, CONF_EXTREME_OFFSET, defaults, DEFAULT_EXTREME_OFFSET
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=8, step=0.1, unit_of_measurement="°C", mode="box"
                )
            ),
            _f(
                vol.Optional, CONF_HOT_OFFSET, defaults, DEFAULT_HOT_OFFSET
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=5, step=0.1, unit_of_measurement="°C", mode="box"
                )
            ),
            _f(
                vol.Optional, CONF_RANGE_OFFSET, defaults, DEFAULT_RANGE_OFFSET
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=5, step=0.1, unit_of_measurement="°C", mode="box"
                )
            ),
            _f(
                vol.Optional, CONF_BELOW_OFFSET, defaults, DEFAULT_BELOW_OFFSET
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=3, step=0.05, unit_of_measurement="°C", mode="box"
                )
            ),
            _f(
                vol.Optional, CONF_TURN_ON_OFFSET, defaults, DEFAULT_TURN_ON_OFFSET
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=5, step=0.1, unit_of_measurement="°C", mode="box"
                )
            ),
            _f(
                vol.Optional, CONF_TEMP_DELTA, defaults, DEFAULT_TEMP_DELTA
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.5, max=5, step=0.5, unit_of_measurement="°C", mode="box"
                )
            ),
            _f(
                vol.Optional, CONF_EXTREME_DELTA, defaults, DEFAULT_EXTREME_DELTA
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.5, max=8, step=0.5, unit_of_measurement="°C", mode="box"
                )
            ),
            _f(
                vol.Optional,
                CONF_PRESENCE_BOOST_ENABLED,
                defaults,
                DEFAULT_PRESENCE_BOOST_ENABLED,
            ): selector.BooleanSelector(),
            _f(
                vol.Optional,
                CONF_PRESENCE_BOOST_MIN,
                defaults,
                DEFAULT_PRESENCE_BOOST_MIN,
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1, max=60, step=1, unit_of_measurement="min", mode="box"
                )
            ),
            _f(
                vol.Optional,
                CONF_PRESENCE_BOOST_OFFSET,
                defaults,
                DEFAULT_PRESENCE_BOOST_OFFSET,
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=5, step=0.1, unit_of_measurement="°C", mode="box"
                )
            ),
            _f(
                vol.Optional, CONF_WINDOW_DELAY_MIN, defaults, DEFAULT_WINDOW_DELAY_MIN
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1, max=60, step=1, unit_of_measurement="min", mode="box"
                )
            ),
            _f(
                vol.Optional,
                CONF_UPDATE_INTERVAL_MIN,
                defaults,
                DEFAULT_UPDATE_INTERVAL_MIN,
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1, max=30, step=1, unit_of_measurement="min", mode="box"
                )
            ),
        }
    )


def _schema_notifiche(defaults: dict) -> vol.Schema:
    return vol.Schema(
        {
            _f(vol.Optional, CONF_TTS_PLAYERS, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="media_player", multiple=True)
            ),
            _f(vol.Optional, CONF_TTS_ENGINE, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="tts")
            ),
            _f(
                vol.Optional, CONF_TTS_MESSAGE_OPEN, defaults, DEFAULT_TTS_MESSAGE_OPEN
            ): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
            _f(vol.Optional, CONF_NOTIFY_TARGETS, defaults): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="notify", multiple=True)
            ),
            _f(vol.Optional, CONF_NOTIFY_CHAT_IDS, defaults): selector.TextSelector(),
            _f(
                vol.Optional, CONF_NOTIFY_MESSAGE, defaults, DEFAULT_NOTIFY_MESSAGE
            ): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
        }
    )


class TermostatoIntelligenteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Flow di configurazione iniziale (4 step)."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_CLIMATE_ENTITY])
            self._abort_if_unique_id_configured()
            self._data.update(user_input)
            return await self.async_step_energia()
        return self.async_show_form(
            step_id="user", data_schema=_schema_user(self._data), errors=errors
        )

    async def async_step_energia(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_soglie()
        return self.async_show_form(
            step_id="energia", data_schema=_schema_energia(self._data)
        )

    async def async_step_soglie(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_notifiche()
        return self.async_show_form(
            step_id="soglie", data_schema=_schema_soglie(self._data)
        )

    async def async_step_notifiche(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(
                title=self._data.get(CONF_NAME, DEFAULT_NAME), data=self._data
            )
        return self.async_show_form(
            step_id="notifiche", data_schema=_schema_notifiche(self._data)
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "TermostatoIntelligenteOptionsFlow":
        return TermostatoIntelligenteOptionsFlow(config_entry)


class TermostatoIntelligenteOptionsFlow(config_entries.OptionsFlow):
    """Permette di rivedere/modificare tutto dopo la configurazione iniziale."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        merged = dict(config_entry.data)
        merged.update(config_entry.options)
        self._data: dict[str, Any] = merged

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        return await self.async_step_energia()

    async def async_step_energia(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_soglie()
        return self.async_show_form(
            step_id="energia", data_schema=_schema_energia(self._data)
        )

    async def async_step_soglie(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_notifiche()
        return self.async_show_form(
            step_id="soglie", data_schema=_schema_soglie(self._data)
        )

    async def async_step_notifiche(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(data=self._data)
        return self.async_show_form(
            step_id="notifiche", data_schema=_schema_notifiche(self._data)
        )
