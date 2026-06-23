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
    CONF_CALIBRATION_MAX_OFFSET,
    CONF_CLIMATE_ENTITY,
    CONF_CONSUMPTION_SENSOR,
    CONF_DOOR_ALERT_ENABLED,
    CONF_DOOR_ALERT_MESSAGE,
    CONF_DOOR_ALERT_NOTIFY,
    CONF_DOOR_ALERT_TTS,
    CONF_DOOR_SENSOR,
    CONF_EXTREME_DELTA,
    CONF_EXTREME_OFFSET,
    CONF_FV_END_TIME,
    CONF_FV_MARGIN_W,
    CONF_FV_PRIORITY,
    CONF_FV_SENSOR,
    CONF_FV_SHUTOFF_DELAY_MIN,
    CONF_FV_SHUTOFF_ENABLED,
    CONF_FV_SHUTOFF_EXTRA_HOURS,
    CONF_FV_STAGGER_MIN,
    CONF_FV_START_TIME,
    CONF_HOT_OFFSET,
    CONF_MIN_BELOW_INTERNAL,
    CONF_NAME,
    CONF_NIGHT_AC_ENABLED,
    CONF_NIGHT_END_TIME,
    CONF_NIGHT_OFFSET,
    CONF_NIGHT_SHUTOFF_DELTA,
    CONF_NIGHT_SHUTOFF_ENABLED,
    CONF_NIGHT_SHUTOFF_MIN,
    CONF_NIGHT_START_TIME,
    CONF_NIGHT_TURN_ON_OFFSET,
    CONF_NOTIFY_CHAT_IDS,
    CONF_NOTIFY_POWER_NOTIFY,
    CONF_NOTIFY_POWER_TTS,
    CONF_NOTIFY_TARGETS,
    CONF_NOTIFY_TEMP_CHANGE_ENABLED,
    CONF_NOTIFY_TEMP_CHANGE_MESSAGE,
    CONF_PRESENCE_BOOST_ENABLED,
    CONF_PRESENCE_BOOST_MIN,
    CONF_PRESENCE_BOOST_OFFSET,
    CONF_PRESENCE_SENSOR,
    CONF_PROFILE,
    CONF_QUIET_ENABLED,
    CONF_QUIET_END_TIME,
    CONF_QUIET_NOTIFY,
    CONF_QUIET_START_TIME,
    CONF_QUIET_TTS,
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
    DEFAULT_BELOW_OFFSET,
    DEFAULT_CALIBRATION_MAX_OFFSET,
    DEFAULT_DOOR_ALERT_ENABLED,
    DEFAULT_DOOR_ALERT_MESSAGE,
    DEFAULT_DOOR_ALERT_NOTIFY,
    DEFAULT_DOOR_ALERT_TTS,
    DEFAULT_EXTREME_DELTA,
    DEFAULT_EXTREME_OFFSET,
    DEFAULT_FV_END_TIME,
    DEFAULT_FV_MARGIN_W,
    DEFAULT_FV_PRIORITY,
    DEFAULT_FV_SHUTOFF_DELAY_MIN,
    DEFAULT_FV_SHUTOFF_ENABLED,
    DEFAULT_FV_SHUTOFF_EXTRA_HOURS,
    DEFAULT_FV_STAGGER_MIN,
    DEFAULT_FV_START_TIME,
    DEFAULT_HOT_OFFSET,
    DEFAULT_MIN_BELOW_INTERNAL,
    DEFAULT_NAME,
    DEFAULT_NIGHT_AC_ENABLED,
    DEFAULT_NIGHT_END_TIME,
    DEFAULT_NIGHT_OFFSET,
    DEFAULT_NIGHT_SHUTOFF_DELTA,
    DEFAULT_NIGHT_SHUTOFF_ENABLED,
    DEFAULT_NIGHT_SHUTOFF_MIN,
    DEFAULT_NIGHT_START_TIME,
    DEFAULT_NIGHT_TURN_ON_OFFSET,
    DEFAULT_NOTIFY_POWER_NOTIFY,
    DEFAULT_NOTIFY_POWER_TTS,
    DEFAULT_NOTIFY_TEMP_CHANGE_ENABLED,
    DEFAULT_NOTIFY_TEMP_CHANGE_MESSAGE,
    DEFAULT_PRESENCE_BOOST_ENABLED,
    DEFAULT_PRESENCE_BOOST_MIN,
    DEFAULT_PRESENCE_BOOST_OFFSET,
    DEFAULT_PROFILE,
    DEFAULT_QUIET_ENABLED,
    DEFAULT_QUIET_END_TIME,
    DEFAULT_QUIET_NOTIFY,
    DEFAULT_QUIET_START_TIME,
    DEFAULT_QUIET_TTS,
    DEFAULT_RANGE_OFFSET,
    DEFAULT_SOC_MIN,
    DEFAULT_TARGET_TEMP,
    DEFAULT_TEMP_DELTA,
    DEFAULT_TTS_MESSAGE_OPEN,
    DEFAULT_TURN_ON_OFFSET,
    DEFAULT_UPDATE_INTERVAL_MIN,
    DEFAULT_WINDOW_DELAY_MIN,
    DOMAIN,
    PRESET_AGGRESSIVO,
    PRESET_BILANCIATO,
    PRESET_DELICATO,
    PRESET_PERSONALIZZATO,
    PRESET_VALUES,
)


def _f(schema_cls, key: str, defaults: dict, fallback: Any = None):
    if key in defaults and defaults[key] not in (None, "", []):
        return schema_cls(key, default=defaults[key])
    if fallback is not None:
        return schema_cls(key, default=fallback)
    return schema_cls(key)


def _schema_user(defaults: dict) -> vol.Schema:
    return vol.Schema({
        _f(vol.Required, CONF_NAME, defaults, DEFAULT_NAME): selector.TextSelector(),
        _f(vol.Required, CONF_CLIMATE_ENTITY, defaults): selector.EntitySelector(selector.EntitySelectorConfig(domain="climate")),
        _f(vol.Required, CONF_TEMP_SENSOR, defaults): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
        _f(vol.Required, CONF_WINDOW_SENSOR, defaults): selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor")),
        _f(vol.Optional, CONF_PRESENCE_SENSOR, defaults): selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor")),
        _f(vol.Optional, CONF_DOOR_SENSOR, defaults): selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor")),
    })


def _schema_sensori(defaults: dict) -> vol.Schema:
    return vol.Schema({
        _f(vol.Optional, CONF_NAME, defaults, DEFAULT_NAME): selector.TextSelector(),
        _f(vol.Required, CONF_TEMP_SENSOR, defaults): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
        _f(vol.Required, CONF_WINDOW_SENSOR, defaults): selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor")),
        _f(vol.Optional, CONF_PRESENCE_SENSOR, defaults): selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor")),
        _f(vol.Optional, CONF_DOOR_SENSOR, defaults): selector.EntitySelector(selector.EntitySelectorConfig(domain="binary_sensor")),
    })


def _schema_energia(defaults: dict) -> vol.Schema:
    return vol.Schema({
        _f(vol.Optional, CONF_FV_SENSOR, defaults): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
        _f(vol.Optional, CONF_CONSUMPTION_SENSOR, defaults): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
        _f(vol.Optional, CONF_BATTERY_SENSOR, defaults): selector.EntitySelector(selector.EntitySelectorConfig(domain="sensor")),
        _f(vol.Optional, CONF_FV_MARGIN_W, defaults, DEFAULT_FV_MARGIN_W): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=5000, step=50, unit_of_measurement="W", mode="box")),
        _f(vol.Optional, CONF_SOC_MIN, defaults, DEFAULT_SOC_MIN): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=100, step=1, unit_of_measurement="%", mode="box")),
        _f(vol.Optional, CONF_FV_START_TIME, defaults, DEFAULT_FV_START_TIME): selector.TimeSelector(),
        _f(vol.Optional, CONF_FV_END_TIME, defaults, DEFAULT_FV_END_TIME): selector.TimeSelector(),
        _f(vol.Optional, CONF_FV_PRIORITY, defaults, DEFAULT_FV_PRIORITY): selector.NumberSelector(selector.NumberSelectorConfig(min=1, max=99, step=1, mode="box")),
        _f(vol.Optional, CONF_FV_STAGGER_MIN, defaults, DEFAULT_FV_STAGGER_MIN): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=60, step=1, unit_of_measurement="min", mode="box")),
        _f(vol.Optional, CONF_FV_SHUTOFF_ENABLED, defaults, DEFAULT_FV_SHUTOFF_ENABLED): selector.BooleanSelector(),
        _f(vol.Optional, CONF_FV_SHUTOFF_DELAY_MIN, defaults, DEFAULT_FV_SHUTOFF_DELAY_MIN): selector.NumberSelector(selector.NumberSelectorConfig(min=1, max=60, step=1, unit_of_measurement="min", mode="box")),
        _f(vol.Optional, CONF_FV_SHUTOFF_EXTRA_HOURS, defaults, DEFAULT_FV_SHUTOFF_EXTRA_HOURS): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=4, step=0.5, unit_of_measurement="h", mode="box")),
    })


def _schema_profilo(defaults: dict) -> vol.Schema:
    return vol.Schema({
        _f(vol.Required, CONF_PROFILE, defaults, DEFAULT_PROFILE): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[PRESET_BILANCIATO, PRESET_AGGRESSIVO, PRESET_DELICATO, PRESET_PERSONALIZZATO],
                mode=selector.SelectSelectorMode.LIST,
                translation_key="profile",
            )
        ),
    })


def _schema_soglie_termiche(defaults: dict) -> vol.Schema:
    return vol.Schema({
        _f(vol.Optional, CONF_TARGET_TEMP_DEFAULT, defaults, DEFAULT_TARGET_TEMP): selector.NumberSelector(selector.NumberSelectorConfig(min=16, max=30, step=0.5, unit_of_measurement="°C", mode="box")),
        _f(vol.Optional, CONF_EXTREME_OFFSET, defaults, DEFAULT_EXTREME_OFFSET): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=8, step=0.1, unit_of_measurement="°C", mode="box")),
        _f(vol.Optional, CONF_HOT_OFFSET, defaults, DEFAULT_HOT_OFFSET): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=5, step=0.1, unit_of_measurement="°C", mode="box")),
        _f(vol.Optional, CONF_RANGE_OFFSET, defaults, DEFAULT_RANGE_OFFSET): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=5, step=0.1, unit_of_measurement="°C", mode="box")),
        _f(vol.Optional, CONF_BELOW_OFFSET, defaults, DEFAULT_BELOW_OFFSET): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=3, step=0.05, unit_of_measurement="°C", mode="box")),
        _f(vol.Optional, CONF_TURN_ON_OFFSET, defaults, DEFAULT_TURN_ON_OFFSET): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=5, step=0.1, unit_of_measurement="°C", mode="box")),
        _f(vol.Optional, CONF_TEMP_DELTA, defaults, DEFAULT_TEMP_DELTA): selector.NumberSelector(selector.NumberSelectorConfig(min=0.5, max=5, step=0.5, unit_of_measurement="°C", mode="box")),
        _f(vol.Optional, CONF_EXTREME_DELTA, defaults, DEFAULT_EXTREME_DELTA): selector.NumberSelector(selector.NumberSelectorConfig(min=0.5, max=8, step=0.5, unit_of_measurement="°C", mode="box")),
    })


def _schema_modalita_notturna(defaults: dict) -> vol.Schema:
    return vol.Schema({
        _f(vol.Optional, CONF_CALIBRATION_MAX_OFFSET, defaults, DEFAULT_CALIBRATION_MAX_OFFSET): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=8, step=0.5, unit_of_measurement="°C", mode="box")),
        _f(vol.Optional, CONF_MIN_BELOW_INTERNAL, defaults, DEFAULT_MIN_BELOW_INTERNAL): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=5, step=0.5, unit_of_measurement="°C", mode="box")),
        _f(vol.Optional, CONF_NIGHT_START_TIME, defaults, DEFAULT_NIGHT_START_TIME): selector.TimeSelector(),
        _f(vol.Optional, CONF_NIGHT_END_TIME, defaults, DEFAULT_NIGHT_END_TIME): selector.TimeSelector(),
        _f(vol.Optional, CONF_NIGHT_OFFSET, defaults, DEFAULT_NIGHT_OFFSET): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=5, step=0.5, unit_of_measurement="°C", mode="box")),
        _f(vol.Optional, CONF_NIGHT_AC_ENABLED, defaults, DEFAULT_NIGHT_AC_ENABLED): selector.BooleanSelector(),
        _f(vol.Optional, CONF_NIGHT_TURN_ON_OFFSET, defaults, DEFAULT_NIGHT_TURN_ON_OFFSET): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=6, step=0.5, unit_of_measurement="°C", mode="box")),
        _f(vol.Optional, CONF_NIGHT_SHUTOFF_ENABLED, defaults, DEFAULT_NIGHT_SHUTOFF_ENABLED): selector.BooleanSelector(),
        _f(vol.Optional, CONF_NIGHT_SHUTOFF_DELTA, defaults, DEFAULT_NIGHT_SHUTOFF_DELTA): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=3, step=0.1, unit_of_measurement="°C", mode="box")),
        _f(vol.Optional, CONF_NIGHT_SHUTOFF_MIN, defaults, DEFAULT_NIGHT_SHUTOFF_MIN): selector.NumberSelector(selector.NumberSelectorConfig(min=5, max=120, step=5, unit_of_measurement="min", mode="box")),
        _f(vol.Optional, CONF_PRESENCE_BOOST_ENABLED, defaults, DEFAULT_PRESENCE_BOOST_ENABLED): selector.BooleanSelector(),
        _f(vol.Optional, CONF_PRESENCE_BOOST_MIN, defaults, DEFAULT_PRESENCE_BOOST_MIN): selector.NumberSelector(selector.NumberSelectorConfig(min=1, max=60, step=1, unit_of_measurement="min", mode="box")),
        _f(vol.Optional, CONF_PRESENCE_BOOST_OFFSET, defaults, DEFAULT_PRESENCE_BOOST_OFFSET): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=5, step=0.1, unit_of_measurement="°C", mode="box")),
        _f(vol.Optional, CONF_WINDOW_DELAY_MIN, defaults, DEFAULT_WINDOW_DELAY_MIN): selector.NumberSelector(selector.NumberSelectorConfig(min=1, max=60, step=1, unit_of_measurement="min", mode="box")),
        _f(vol.Optional, CONF_UPDATE_INTERVAL_MIN, defaults, DEFAULT_UPDATE_INTERVAL_MIN): selector.NumberSelector(selector.NumberSelectorConfig(min=1, max=30, step=1, unit_of_measurement="min", mode="box")),
    })


def _schema_notifiche(defaults: dict) -> vol.Schema:
    return vol.Schema({
        # --- Google Home / TTS ---
        _f(vol.Optional, CONF_TTS_PLAYERS, defaults): selector.EntitySelector(selector.EntitySelectorConfig(domain="media_player", multiple=True)),
        _f(vol.Optional, CONF_TTS_ENGINE, defaults): selector.EntitySelector(selector.EntitySelectorConfig(domain="tts")),
        _f(vol.Optional, CONF_TTS_MESSAGE_OPEN, defaults, DEFAULT_TTS_MESSAGE_OPEN): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
        # --- Telegram / notify ---
        _f(vol.Optional, CONF_NOTIFY_TARGETS, defaults): selector.EntitySelector(selector.EntitySelectorConfig(domain="notify", multiple=True)),
        _f(vol.Optional, CONF_NOTIFY_CHAT_IDS, defaults): selector.TextSelector(),
        _f(vol.Optional, CONF_NOTIFY_TEMP_CHANGE_ENABLED, defaults, DEFAULT_NOTIFY_TEMP_CHANGE_ENABLED): selector.BooleanSelector(),
        _f(vol.Optional, CONF_NOTIFY_TEMP_CHANGE_MESSAGE, defaults, DEFAULT_NOTIFY_TEMP_CHANGE_MESSAGE): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
        # --- Avvisi accensione/spegnimento automatico ---
        _f(vol.Optional, CONF_NOTIFY_POWER_TTS, defaults, DEFAULT_NOTIFY_POWER_TTS): selector.BooleanSelector(),
        _f(vol.Optional, CONF_NOTIFY_POWER_NOTIFY, defaults, DEFAULT_NOTIFY_POWER_NOTIFY): selector.BooleanSelector(),
        # --- Avviso porta (apertura e chiusura) ---
        _f(vol.Optional, CONF_DOOR_ALERT_ENABLED, defaults, DEFAULT_DOOR_ALERT_ENABLED): selector.BooleanSelector(),
        _f(vol.Optional, CONF_DOOR_ALERT_TTS, defaults, DEFAULT_DOOR_ALERT_TTS): selector.BooleanSelector(),
        _f(vol.Optional, CONF_DOOR_ALERT_NOTIFY, defaults, DEFAULT_DOOR_ALERT_NOTIFY): selector.BooleanSelector(),
        _f(vol.Optional, CONF_DOOR_ALERT_MESSAGE, defaults, DEFAULT_DOOR_ALERT_MESSAGE): selector.TextSelector(selector.TextSelectorConfig(multiline=True)),
        # --- Fascia di silenzio (integrata in notifiche) ---
        _f(vol.Optional, CONF_QUIET_ENABLED, defaults, DEFAULT_QUIET_ENABLED): selector.BooleanSelector(),
        _f(vol.Optional, CONF_QUIET_START_TIME, defaults, DEFAULT_QUIET_START_TIME): selector.TimeSelector(),
        _f(vol.Optional, CONF_QUIET_END_TIME, defaults, DEFAULT_QUIET_END_TIME): selector.TimeSelector(),
        _f(vol.Optional, CONF_QUIET_TTS, defaults, DEFAULT_QUIET_TTS): selector.BooleanSelector(),
        _f(vol.Optional, CONF_QUIET_NOTIFY, defaults, DEFAULT_QUIET_NOTIFY): selector.BooleanSelector(),
    })


def _schema_silenzio(defaults: dict) -> vol.Schema:
    return vol.Schema({
        _f(vol.Optional, CONF_QUIET_ENABLED, defaults, DEFAULT_QUIET_ENABLED): selector.BooleanSelector(),
        _f(vol.Optional, CONF_QUIET_START_TIME, defaults, DEFAULT_QUIET_START_TIME): selector.TimeSelector(),
        _f(vol.Optional, CONF_QUIET_END_TIME, defaults, DEFAULT_QUIET_END_TIME): selector.TimeSelector(),
        _f(vol.Optional, CONF_QUIET_TTS, defaults, DEFAULT_QUIET_TTS): selector.BooleanSelector(),
        _f(vol.Optional, CONF_QUIET_NOTIFY, defaults, DEFAULT_QUIET_NOTIFY): selector.BooleanSelector(),
    })


class TermostatoIntelligenteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_CLIMATE_ENTITY])
            self._abort_if_unique_id_configured()
            self._data.update(user_input)
            return await self.async_step_energia()
        return self.async_show_form(step_id="user", data_schema=_schema_user(self._data), errors=errors)

    async def async_step_energia(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_profilo()
        return self.async_show_form(step_id="energia", data_schema=_schema_energia(self._data))

    async def async_step_profilo(self, user_input=None):
        if user_input is not None:
            profile = user_input[CONF_PROFILE]
            self._data[CONF_PROFILE] = profile
            if profile in PRESET_VALUES:
                self._data.update(PRESET_VALUES[profile])
                return await self.async_step_notifiche()
            return await self.async_step_soglie_termiche()
        return self.async_show_form(step_id="profilo", data_schema=_schema_profilo(self._data))

    async def async_step_soglie_termiche(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_modalita_notturna()
        return self.async_show_form(step_id="soglie_termiche", data_schema=_schema_soglie_termiche(self._data))

    async def async_step_modalita_notturna(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_notifiche()
        return self.async_show_form(step_id="modalita_notturna", data_schema=_schema_modalita_notturna(self._data))

    async def async_step_notifiche(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title=self._data.get(CONF_NAME, DEFAULT_NAME), data=self._data)
        return self.async_show_form(step_id="notifiche", data_schema=_schema_notifiche(self._data))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return TermostatoIntelligenteOptionsFlow(config_entry)


class TermostatoIntelligenteOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry) -> None:
        merged = dict(config_entry.data)
        merged.update(config_entry.options)
        if CONF_PROFILE not in merged:
            merged[CONF_PROFILE] = PRESET_PERSONALIZZATO
        self._data: dict[str, Any] = merged

    async def async_step_init(self, user_input=None):
        return await self.async_step_sensori()

    async def async_step_sensori(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_energia()
        return self.async_show_form(step_id="sensori", data_schema=_schema_sensori(self._data))

    async def async_step_energia(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_profilo()
        return self.async_show_form(step_id="energia", data_schema=_schema_energia(self._data))

    async def async_step_profilo(self, user_input=None):
        if user_input is not None:
            profile = user_input[CONF_PROFILE]
            self._data[CONF_PROFILE] = profile
            if profile in PRESET_VALUES:
                self._data.update(PRESET_VALUES[profile])
                return await self.async_step_notifiche()
            return await self.async_step_soglie_termiche()
        return self.async_show_form(step_id="profilo", data_schema=_schema_profilo(self._data))

    async def async_step_soglie_termiche(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_modalita_notturna()
        return self.async_show_form(step_id="soglie_termiche", data_schema=_schema_soglie_termiche(self._data))

    async def async_step_modalita_notturna(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_notifiche()
        return self.async_show_form(step_id="modalita_notturna", data_schema=_schema_modalita_notturna(self._data))

    async def async_step_notifiche(self, user_input=None):
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(data=self._data)
        return self.async_show_form(step_id="notifiche", data_schema=_schema_notifiche(self._data))
