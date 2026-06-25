"""Piattaforma climate: il vero e proprio 'termostato intelligente'."""

from __future__ import annotations

import logging
import math
from datetime import datetime, time as dt_time, timedelta
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import Event, HomeAssistant, State
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.template import Template
from homeassistant.util import dt as dt_util

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
    CONF_FV_SHUTOFF_THRESHOLD,
    CONF_FV_STAGGER_MIN,
    CONF_FV_START_TIME,
    CONF_HOT_OFFSET,
    CONF_MIN_BELOW_INTERNAL,
    CONF_NAME,
    CONF_NIGHT_AC_ENABLED,
    CONF_NIGHT_END_TIME,
    CONF_NIGHT_END_SHUTOFF_AUTO_ONLY,
    CONF_NIGHT_END_SHUTOFF_ENABLED,
    CONF_NIGHT_OFFSET,
    CONF_NIGHT_SHUTOFF_DELTA,
    CONF_NIGHT_SHUTOFF_ENABLED,
    CONF_NIGHT_SHUTOFF_MIN,
    CONF_NIGHT_START_TIME,
    CONF_NIGHT_TURN_ON_OFFSET,
    CONF_NOTIFY_CHAT_IDS,
    CONF_NOTIFY_NIGHT_END_NOTIFY,
    CONF_NOTIFY_NIGHT_END_TTS,
    CONF_NOTIFY_POWER_NOTIFY,
    CONF_NOTIFY_POWER_TTS,
    CONF_NOTIFY_TARGETS,
    CONF_NOTIFY_TEMP_CHANGE_ENABLED,
    CONF_NOTIFY_TEMP_CHANGE_LIMIT_ENABLED,
    CONF_NOTIFY_TEMP_CHANGE_LIMIT_MIN,
    CONF_NOTIFY_TEMP_CHANGE_MESSAGE,
    CONF_PRESENCE_BOOST_ENABLED,
    CONF_PRESENCE_BOOST_MIN,
    CONF_PRESENCE_BOOST_OFFSET,
    CONF_PRESENCE_SENSOR,
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
    DEFAULT_FV_SHUTOFF_THRESHOLD,
    DEFAULT_FV_STAGGER_MIN,
    DEFAULT_FV_START_TIME,
    DEFAULT_HOT_OFFSET,
    DEFAULT_MIN_BELOW_INTERNAL,
    DEFAULT_NAME,
    DEFAULT_NIGHT_AC_ENABLED,
    DEFAULT_NIGHT_END_TIME,
    DEFAULT_NIGHT_END_SHUTOFF_AUTO_ONLY,
    DEFAULT_NIGHT_END_SHUTOFF_ENABLED,
    DEFAULT_NIGHT_OFFSET,
    DEFAULT_NIGHT_SHUTOFF_DELTA,
    DEFAULT_NIGHT_SHUTOFF_ENABLED,
    DEFAULT_NIGHT_SHUTOFF_MIN,
    DEFAULT_NIGHT_START_TIME,
    DEFAULT_NIGHT_TURN_ON_OFFSET,
    DEFAULT_DOOR_ALERT_CLOSED_MESSAGE,
    DEFAULT_DOOR_ALERT_OPEN_MESSAGE,
    DEFAULT_NOTIFY_MESSAGE_CLOSED,
    DEFAULT_NOTIFY_MESSAGE_OPEN,
    DEFAULT_NOTIFY_NIGHT_END_NOTIFY,
    DEFAULT_NOTIFY_NIGHT_END_TTS,
    DEFAULT_NOTIFY_POWER_NOTIFY,
    DEFAULT_NOTIFY_POWER_TTS,
    DEFAULT_NOTIFY_TEMP_CHANGE_ENABLED,
    DEFAULT_NOTIFY_TEMP_CHANGE_LIMIT_ENABLED,
    DEFAULT_NOTIFY_TEMP_CHANGE_LIMIT_MIN,
    DEFAULT_NOTIFY_TEMP_CHANGE_MESSAGE,
    DEFAULT_POWER_OFF_FV_MESSAGE,
    DEFAULT_POWER_OFF_NIGHT_END_MESSAGE,
    DEFAULT_POWER_OFF_NIGHT_MESSAGE,
    DEFAULT_POWER_ON_FV_MESSAGE,
    DEFAULT_POWER_ON_NIGHT_MESSAGE,
    DEFAULT_PRESENCE_BOOST_ENABLED,
    DEFAULT_PRESENCE_BOOST_MIN,
    DEFAULT_PRESENCE_BOOST_OFFSET,
    DEFAULT_QUIET_ENABLED,
    DEFAULT_QUIET_END_TIME,
    DEFAULT_QUIET_NOTIFY,
    DEFAULT_QUIET_START_TIME,
    DEFAULT_QUIET_TTS,
    DEFAULT_RANGE_OFFSET,
    DEFAULT_SOC_MIN,
    DEFAULT_TARGET_TEMP,
    DEFAULT_TEMP_DELTA,
    DEFAULT_TTS_MESSAGE_CLOSED,
    DEFAULT_TTS_MESSAGE_OPEN,
    DEFAULT_TURN_ON_OFFSET,
    DEFAULT_UPDATE_INTERVAL_MIN,
    DEFAULT_WINDOW_DELAY_MIN,
    DOMAIN,
    FAN_MODES_ALLOWED,
    REASON_FV,
    REASON_FV_SHUTOFF,
    REASON_NIGHT,
    REASON_NIGHT_END,
    REASON_NIGHT_SHUTOFF,
    SWITCH_KEY_FV,
    SWITCH_KEY_MASTER,
    SWITCH_KEY_QUICK,
)
from .const import (
    CONF_CONFIG_MODE,
    CONF_SIMPLE_NIGHT_END,
    CONF_SIMPLE_NIGHT_START,
    CONF_SIMPLE_SUNSET_ANTICIPATE_H,
    CONF_SIMPLE_NOTIFY_AC_OFF,
    CONF_SIMPLE_NOTIFY_AC_ON,
    CONF_SIMPLE_NOTIFY_DOOR_CLOSE,
    CONF_SIMPLE_NOTIFY_DOOR_OPEN,
    CONF_SIMPLE_NOTIFY_NIGHT_END,
    CONF_SIMPLE_NOTIFY_NIGHT_START,
    CONF_SIMPLE_NOTIFY_WINDOW_CLOSE,
    CONF_SIMPLE_NOTIFY_WINDOW_OPEN,
    CONF_SIMPLE_QUIET_NIGHT_NOTIFY,
    CONF_SIMPLE_QUIET_NIGHT_TTS,
    CONF_SIMPLE_TARGET_DAY,
    CONF_SIMPLE_TARGET_NIGHT,
    CONF_SIMPLE_DRY_ENABLED,
    CONF_SIMPLE_DRY_MAX_MIN,
    CONFIG_MODE_FULL,
    CONFIG_MODE_SIMPLE,
    CONFIG_MODE_SIMPLE_FV,
    DEFAULT_SIMPLE_DRY_ENABLED,
    DEFAULT_SIMPLE_DRY_MAX_MIN,
    DEFAULT_SIMPLE_DAY_END,
    DEFAULT_SIMPLE_DAY_START,
    DEFAULT_SIMPLE_MSG_AC_OFF,
    DEFAULT_SIMPLE_MSG_AC_ON,
    DEFAULT_SIMPLE_MSG_DOOR_CLOSE,
    DEFAULT_SIMPLE_MSG_DOOR_OPEN,
    DEFAULT_SIMPLE_MSG_NIGHT_END,
    DEFAULT_SIMPLE_MSG_NIGHT_START,
    DEFAULT_SIMPLE_MSG_WINDOW_CLOSE,
    DEFAULT_SIMPLE_MSG_WINDOW_OPEN,
    DEFAULT_SIMPLE_NIGHT_END,
    DEFAULT_SIMPLE_NIGHT_START,
    DEFAULT_SIMPLE_SUNSET_ANTICIPATE_H,
    DEFAULT_SIMPLE_NOTIFY_AC_OFF,
    DEFAULT_SIMPLE_NOTIFY_AC_ON,
    DEFAULT_SIMPLE_NOTIFY_DOOR_CLOSE,
    DEFAULT_SIMPLE_NOTIFY_DOOR_OPEN,
    DEFAULT_SIMPLE_NOTIFY_NIGHT_END,
    DEFAULT_SIMPLE_NOTIFY_NIGHT_START,
    DEFAULT_SIMPLE_NOTIFY_WINDOW_CLOSE,
    DEFAULT_SIMPLE_NOTIFY_WINDOW_OPEN,
    DEFAULT_SIMPLE_QUIET_NIGHT_NOTIFY,
    DEFAULT_SIMPLE_QUIET_NIGHT_TTS,
    DEFAULT_SIMPLE_TARGET_DAY,
    DEFAULT_SIMPLE_TARGET_NIGHT,
    SIMPLE_EXT_DRY_HIGH,
    SIMPLE_EXT_DRY_LOW,
    SIMPLE_EXT_HOT_OFFSET,
    SIMPLE_EXT_MILD_OFFSET,
    SIMPLE_EXT_SETPOINT_HOT,
    SIMPLE_EXT_SETPOINT_MILD,
    SIMPLE_EXT_SHUTOFF_MIN,
    SIMPLE_EXT_SHUTOFF_OFFSET,
    SIMPLE_EXT_SLOW_OFFSET,
    SIMPLE_EXT_TURN_ON_OFFSET,
    SIMPLE_EXT_WARM_OFFSET,
    SIMPLE_INT_DRY_HIGH,
    SIMPLE_INT_DRY_LOW,
    SIMPLE_INT_AT_TARGET,
    SIMPLE_INT_HOT_OFFSET,
    SIMPLE_INT_SETPOINT_HOT,
    SIMPLE_INT_SETPOINT_MILD,
    SIMPLE_INT_SHUTOFF_MIN,
    SIMPLE_INT_SHUTOFF_OFFSET,
    SIMPLE_INT_TURN_ON_OFFSET,
    SIMPLE_INT_WARM_OFFSET,
    SIMPLE_WINDOW_DELAY_MIN,
)
from .util import get_conf

_LOGGER = logging.getLogger(__name__)

# Stati considerati "non validi" per le transizioni sensori
_INVALID_STATES = {"unknown", "unavailable"}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([SmartFvClimate(hass, entry)])


class SmartFvClimate(ClimateEntity, RestoreEntity):
    """Termostato intelligente FV con avvisi accensione/spegnimento e fascia silenzio."""

    _attr_should_poll = False
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.COOL]
    _attr_fan_modes = FAN_MODES_ALLOWED
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = entry.entry_id
        self._attr_name = get_conf(entry, CONF_NAME, DEFAULT_NAME)
        self._climate_entity: str = get_conf(entry, CONF_CLIMATE_ENTITY)
        self._temp_sensor: str = get_conf(entry, CONF_TEMP_SENSOR)
        self._window_sensor: str | None = get_conf(entry, CONF_WINDOW_SENSOR)
        self._presence_sensor: str | None = get_conf(entry, CONF_PRESENCE_SENSOR)
        self._door_sensor: str | None = get_conf(entry, CONF_DOOR_SENSOR)
        self._fv_sensor: str | None = get_conf(entry, CONF_FV_SENSOR)
        self._consumption_sensor: str | None = get_conf(entry, CONF_CONSUMPTION_SENSOR)
        self._battery_sensor: str | None = get_conf(entry, CONF_BATTERY_SENSOR)
        self._target_temperature: float = float(
            get_conf(entry, CONF_TARGET_TEMP_DEFAULT, DEFAULT_TARGET_TEMP)
        )
        self._snapshot: dict[str, Any] | None = None
        self._window_cancel_timer = None
        self._presence_since: datetime | None = None

        # --- Sliding window FV shutoff ---
        self._fv_surplus_buffer: list[float] = []

        self._night_below_since: datetime | None = None

        # --- Fine modalità notturna ---
        # Traccia se eravamo in modalità notte al ciclo precedente
        # (per rilevare la transizione notte→giorno)
        self._was_night_mode: bool = False
        # Traccia se il clima è stato acceso automaticamente dalla modalità notturna
        self._night_auto_on: bool = False

        # --- Limite notifiche cambio temperatura ---
        self._last_temp_notify: datetime | None = None

        # --- Modo semplificato ---
        self._simple_shutoff_since: datetime | None = None  # timer spegnimento per target raggiunto
        self._simple_was_night: bool = False                 # per rilevare transizione notte→giorno
        self._simple_night_auto_on: bool = False             # acceso automaticamente di notte
        self._simple_dry_since: datetime | None = None       # da quando è in modalità dry
        self._fv_auto_on: bool = False                       # acceso automaticamente dal FV

        hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {})["climate"] = self

    # ------------------------------------------------------------------
    # Proprietà
    # ------------------------------------------------------------------

    @property
    def current_temperature(self) -> float | None:
        return self._read_float(self._temp_sensor)

    @property
    def target_temperature(self) -> float:
        return self._target_temperature

    @property
    def hvac_mode(self) -> HVACMode:
        state = self.hass.states.get(self._climate_entity)
        if state is None or state.state in ("unknown", "unavailable", "off"):
            return HVACMode.OFF
        return HVACMode.COOL

    @property
    def fan_mode(self) -> str | None:
        state = self.hass.states.get(self._climate_entity)
        if state is None:
            return None
        return state.attributes.get("fan_mode")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "finestra_aperta": self._is_window_open(),
            "porta_aperta": self._is_door_open(),
            "snapshot_attivo": self._snapshot is not None,
            "presenza_da": self._presence_since.isoformat() if self._presence_since else None,
            "climatizzatore_reale": self._climate_entity,
            "termostato_abilitato": self._switch_state(SWITCH_KEY_MASTER, True),
            "accensione_fv_abilitata": self._switch_state(SWITCH_KEY_FV, True),
            "raffreddamento_rapido": self._switch_state(SWITCH_KEY_QUICK, False),
            "modalita_notturna_attiva": self._is_night_mode_active(),
            "target_effettivo": self._effective_target(),
            "accensione_notturna_abilitata": bool(
                get_conf(self.entry, CONF_NIGHT_AC_ENABLED, DEFAULT_NIGHT_AC_ENABLED)
            ),
            "spegnimento_fv_abilitato": bool(
                get_conf(self.entry, CONF_FV_SHUTOFF_ENABLED, DEFAULT_FV_SHUTOFF_ENABLED)
            ),
            "spegnimento_notturno_abilitato": bool(
                get_conf(self.entry, CONF_NIGHT_SHUTOFF_ENABLED, DEFAULT_NIGHT_SHUTOFF_ENABLED)
            ),
            "spegnimento_fine_notte_abilitato": bool(
                get_conf(self.entry, CONF_NIGHT_END_SHUTOFF_ENABLED, DEFAULT_NIGHT_END_SHUTOFF_ENABLED)
            ),
            "accensione_notturna_automatica": self._night_auto_on,
            "fv_surplus_buffer": self._fv_surplus_buffer,
            "notte_sotto_target_da": self._night_below_since.isoformat() if self._night_below_since else None,
            "fascia_silenzio_attiva": self._is_quiet_time(),
        }

    # ------------------------------------------------------------------
    # Ciclo di vita
    # ------------------------------------------------------------------

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None:
            temp_attr = last_state.attributes.get(ATTR_TEMPERATURE)
            if temp_attr is not None:
                try:
                    self._target_temperature = float(temp_attr)
                except (TypeError, ValueError):
                    pass
        if self._presence_sensor:
            presence_state = self.hass.states.get(self._presence_sensor)
            if presence_state and presence_state.state == "on":
                self._presence_since = presence_state.last_changed
        # Inizializza _was_night_mode con lo stato attuale così al primo ciclo
        # non scatta uno spegnimento fasullo se HA si riavvia durante la notte
        self._was_night_mode = self._is_night_mode_active()
        # Stesso per il modo semplificato
        self._simple_was_night = self._simple_is_night()
        interval_min = int(get_conf(self.entry, CONF_UPDATE_INTERVAL_MIN, DEFAULT_UPDATE_INTERVAL_MIN))
        self.async_on_remove(
            async_track_time_interval(self.hass, self._async_periodic_update, timedelta(minutes=interval_min))
        )
        tracked = [e for e in (self._climate_entity, self._temp_sensor, self._window_sensor, self._presence_sensor, self._door_sensor) if e]
        if tracked:
            self.async_on_remove(async_track_state_change_event(self.hass, tracked, self._async_on_state_change))

    async def _async_on_state_change(self, event: Event) -> None:
        entity_id = event.data.get("entity_id")
        new_state: State | None = event.data.get("new_state")
        old_state: State | None = event.data.get("old_state")

        if entity_id == self._window_sensor:
            await self._async_handle_window(new_state, old_state)
        elif entity_id == self._door_sensor:
            await self._async_handle_door(new_state, old_state)
        elif entity_id == self._presence_sensor:
            if new_state and new_state.state == "on":
                if old_state is None or old_state.state != "on":
                    self._presence_since = new_state.last_changed
            else:
                self._presence_since = None
        elif entity_id == self._climate_entity:
            if new_state and new_state.state in ("off", "unknown", "unavailable"):
                self._fv_surplus_buffer = []
                self._night_below_since = None
                self._night_auto_on = False  # clima spento: reset flag accensione notte
                self._fv_auto_on = False     # reset flag accensione FV
                self._simple_night_auto_on = False
                self._simple_dry_since = None
                self._simple_shutoff_since = None
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        if self._window_cancel_timer is not None:
            self._window_cancel_timer()
            self._window_cancel_timer = None
        data = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {})
        if data.get("climate") is self:
            data.pop("climate", None)

    # ------------------------------------------------------------------
    # Comandi utente
    # ------------------------------------------------------------------

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        self._target_temperature = float(temperature)
        self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        if fan_mode not in FAN_MODES_ALLOWED:
            fan_mode = FAN_MODES_ALLOWED[0]
        await self.hass.services.async_call("climate", "set_fan_mode", {"entity_id": self._climate_entity, "fan_mode": fan_mode}, blocking=True)
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        service = "turn_on" if hvac_mode == HVACMode.COOL else "turn_off"
        await self.hass.services.async_call("climate", service, {"entity_id": self._climate_entity}, blocking=True)
        self.async_write_ha_state()

    # ------------------------------------------------------------------
    # Loop periodico
    # ------------------------------------------------------------------

    async def _async_periodic_update(self, now: datetime | None = None) -> None:
        if not self._switch_state(SWITCH_KEY_MASTER, True):
            return
        if self._is_window_open():
            return

        mode = get_conf(self.entry, CONF_CONFIG_MODE, CONFIG_MODE_FULL)

        if mode in (CONFIG_MODE_SIMPLE, CONFIG_MODE_SIMPLE_FV):
            await self._async_periodic_update_simple(now)
        else:
            await self._async_periodic_update_full(now)

        self.async_write_ha_state()

    async def _async_periodic_update_full(self, now: datetime | None = None) -> None:
        """Loop periodico per il modo completo."""
        temp = self.current_temperature
        if temp is None:
            return
        target = self._effective_target()

        # Rileva transizione notte → giorno PRIMA di aggiornare _was_night_mode
        night_now = self._is_night_mode_active()
        night_just_ended = self._was_night_mode and not night_now
        self._was_night_mode = night_now

        await self._async_handle_thermal(temp, target)

        if self._switch_state(SWITCH_KEY_FV, True) and self._within_fv_window():
            await self._async_handle_fv_turn_on(temp, target)

        if night_now and bool(get_conf(self.entry, CONF_NIGHT_AC_ENABLED, DEFAULT_NIGHT_AC_ENABLED)):
            await self._async_handle_night_turn_on(temp, target)

        if bool(get_conf(self.entry, CONF_FV_SHUTOFF_ENABLED, DEFAULT_FV_SHUTOFF_ENABLED)):
            await self._async_handle_fv_shutoff(temp, target)

        if night_now and bool(get_conf(self.entry, CONF_NIGHT_SHUTOFF_ENABLED, DEFAULT_NIGHT_SHUTOFF_ENABLED)):
            await self._async_handle_night_shutoff(temp, target)

        # Spegnimento a fine modalità notturna
        if night_just_ended:
            await self._async_handle_night_end_shutoff()

        await self._async_handle_presence_boost(temp, target)

    # ------------------------------------------------------------------
    # Loop periodico — Modo semplificato
    # ------------------------------------------------------------------

    async def _async_periodic_update_simple(self, now: datetime | None = None) -> None:
        """Loop periodico per modo semplificato e semplificato con FV."""
        use_internal = not bool(self._temp_sensor)
        temp = self._simple_read_temp()
        if temp is None:
            return

        night_now = self._simple_is_night()
        night_just_ended = self._simple_was_night and not night_now
        night_just_started = not self._simple_was_night and night_now
        self._simple_was_night = night_now

        target = self._simple_current_target()

        # Notifica inizio modalità notturna
        if night_just_started:
            await self._async_simple_notify_night_start(target)

        # Regolazione termica
        await self._async_handle_thermal_simple(temp, target, use_internal)

        # Accensione e spegnimento automatico (solo modo semplificato con FV)
        mode = get_conf(self.entry, CONF_CONFIG_MODE, CONFIG_MODE_FULL)
        if mode == CONFIG_MODE_SIMPLE_FV:
            if self._switch_state(SWITCH_KEY_FV, True) and self._within_fv_window():
                await self._async_handle_fv_turn_on_simple(temp, target)
            if bool(get_conf(self.entry, CONF_FV_SHUTOFF_ENABLED, DEFAULT_FV_SHUTOFF_ENABLED)):
                await self._async_handle_fv_shutoff_simple(temp, target)

        # Spegnimento fine notte
        if night_just_ended:
            await self._async_handle_night_end_shutoff()
            await self._async_simple_notify_night_end()

    def _simple_read_temp(self) -> float | None:
        """Legge la temperatura: sonda esterna se configurata, altrimenti sonda interna del clima."""
        if self._temp_sensor:
            return self._read_float(self._temp_sensor)
        # Usa current_temperature dagli attributi del climatizzatore reale
        state = self.hass.states.get(self._climate_entity)
        if state is None:
            return None
        raw = state.attributes.get("current_temperature")
        if raw is None:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    def _simple_is_night(self) -> bool:
        return self._in_time_window(
            get_conf(self.entry, CONF_SIMPLE_NIGHT_START, DEFAULT_SIMPLE_NIGHT_START),
            get_conf(self.entry, CONF_SIMPLE_NIGHT_END, DEFAULT_SIMPLE_NIGHT_END),
        )

    def _simple_can_control_manual(self) -> bool:
        """Restituisce True se l'automazione può spegnere il clima acceso manualmente.

        Condizioni:
        - Il sole è sopra l'orizzonte (sun.sun == above_horizon)
        - Siamo almeno X ore prima del tramonto (configurabile, min 2h)
        """
        sun_state = self.hass.states.get("sun.sun")
        if sun_state is None:
            return False  # sun.sun non disponibile → non intervenire

        # Sole sotto l'orizzonte → non intervenire
        if sun_state.state != "above_horizon":
            return False

        # Calcola orario tramonto
        next_setting_str = sun_state.attributes.get("next_setting")
        if not next_setting_str:
            return False
        try:
            next_setting = dt_util.parse_datetime(str(next_setting_str))
            if next_setting is None:
                return False
            sunset_local = dt_util.as_local(next_setting)
        except (ValueError, TypeError):
            return False

        anticipate_h = float(get_conf(self.entry, CONF_SIMPLE_SUNSET_ANTICIPATE_H, DEFAULT_SIMPLE_SUNSET_ANTICIPATE_H))
        cutoff = sunset_local - timedelta(hours=anticipate_h)
        now_local = dt_util.now()

        return now_local < cutoff

    def _simple_current_target(self) -> float:
        if self._simple_is_night():
            return float(get_conf(self.entry, CONF_SIMPLE_TARGET_NIGHT, DEFAULT_SIMPLE_TARGET_NIGHT))
        return float(get_conf(self.entry, CONF_SIMPLE_TARGET_DAY, DEFAULT_SIMPLE_TARGET_DAY))

    def _simple_is_quiet_night(self) -> bool:
        """Fascia di silenzio notturna semplificata = stessa fascia notturna."""
        return self._simple_is_night()

    async def _async_handle_thermal_simple(
        self, temp: float, target: float, use_internal: bool
    ) -> None:
        """Logica termica per il modo semplificato.

        use_internal=True  → sonda interna (valori interi, soglie intere)
        use_internal=False → sonda esterna (valori decimali, soglie decimali)
        """
        real_state = self.hass.states.get(self._climate_entity)
        internal_temp: float | None = None
        if real_state is not None:
            raw = real_state.attributes.get("current_temperature")
            if raw is not None:
                try:
                    internal_temp = float(raw)
                except (TypeError, ValueError):
                    pass

        dry_enabled = bool(get_conf(self.entry, CONF_SIMPLE_DRY_ENABLED, DEFAULT_SIMPLE_DRY_ENABLED))

        if use_internal:
            await self._async_thermal_simple_internal(temp, target, internal_temp, real_state, dry_enabled)
        else:
            await self._async_thermal_simple_external(temp, target, internal_temp, real_state, dry_enabled)

    async def _async_thermal_simple_internal(
        self, temp: float, target: float, internal_temp: float | None, real_state, dry_enabled: bool
    ) -> None:
        """Logica termica con sonda interna (interi).

        Senza dry:
          Accende in COOL se temp > target + 2
        Con dry:
          Accende in DRY se temp > target + 1, passa a COOL se temp > target + 2
          oppure dopo dry_max_min minuti in dry

        Spegne se temp <= target - 1 per 15 min consecutivi.
        """
        dry_max_min = int(get_conf(self.entry, CONF_SIMPLE_DRY_MAX_MIN, DEFAULT_SIMPLE_DRY_MAX_MIN))
        now = dt_util.utcnow()
        current_mode = real_state.state if real_state else "off"
        is_on = self.hvac_mode == HVACMode.COOL or current_mode == "dry"

        # --- Spegnimento per target raggiunto ---
        if is_on:
            shutoff_threshold = target + SIMPLE_INT_SHUTOFF_OFFSET  # target - 1
            if temp <= shutoff_threshold:
                if self._simple_shutoff_since is None:
                    self._simple_shutoff_since = now
                elif (now - self._simple_shutoff_since) >= timedelta(minutes=SIMPLE_INT_SHUTOFF_MIN):
                    _LOGGER.info("%s: [semplificato] spegnimento target raggiunto (int, temp=%.0f)", self._attr_name, temp)
                    await self.hass.services.async_call("climate", "turn_off", {"entity_id": self._climate_entity}, blocking=True)
                    self._simple_shutoff_since = None
                    self._simple_dry_since = None
                    self._simple_night_auto_on = False
                    self._fv_auto_on = False
                    await self._async_simple_notify_ac_off(temp, target)
                    return
            else:
                self._simple_shutoff_since = None

        # --- Passaggio da DRY a COOL ---
        if dry_enabled and current_mode == "dry":
            dry_elapsed = (now - self._simple_dry_since) if self._simple_dry_since else timedelta(0)
            should_switch_cool = (
                temp > target + SIMPLE_INT_DRY_HIGH or
                dry_elapsed >= timedelta(minutes=dry_max_min)
            )
            if should_switch_cool:
                _LOGGER.info("%s: [semplificato] DRY→COOL (int, temp=%.0f, elapsed=%s)", self._attr_name, temp, dry_elapsed)
                await self.hass.services.async_call("climate", "turn_on", {"entity_id": self._climate_entity}, blocking=True)
                self._simple_dry_since = None
            else:
                _LOGGER.debug("%s: [semplificato] in DRY (int, temp=%.0f, elapsed=%s)", self._attr_name, temp, dry_elapsed)
                return  # rimane in dry, niente da fare

        # --- Accensione ---
        if not is_on:
            if dry_enabled and temp > target + SIMPLE_INT_DRY_LOW and temp <= target + SIMPLE_INT_DRY_HIGH:
                # Fascia dry: accende in deumidificazione
                _LOGGER.info("%s: [semplificato] accensione DRY (int, temp=%.0f)", self._attr_name, temp)
                await self.hass.services.async_call("climate", "set_hvac_mode", {"entity_id": self._climate_entity, "hvac_mode": "dry"}, blocking=True)
                self._simple_dry_since = now
                self._simple_night_auto_on = self._simple_is_night()
                self._fv_auto_on = False
                await self._async_simple_notify_ac_on(temp)
                return
            elif temp > target + SIMPLE_INT_TURN_ON_OFFSET:
                # Sopra soglia cool: accende direttamente in raffreddamento
                _LOGGER.info("%s: [semplificato] accensione COOL diretta (int, temp=%.0f)", self._attr_name, temp)
                await self.hass.services.async_call("climate", "turn_on", {"entity_id": self._climate_entity}, blocking=True)
                self._simple_dry_since = None
                self._simple_night_auto_on = self._simple_is_night()
                self._fv_auto_on = False
                await self._async_simple_notify_ac_on(temp)
            return  # se ancora OFF non regolare

        # --- Regolazione termica (clima in COOL) ---
        if internal_temp is None:
            return

        if temp > target + SIMPLE_INT_HOT_OFFSET:
            new_setpoint = int(internal_temp) - SIMPLE_INT_SETPOINT_HOT
            fan = "high"
        elif temp > target + SIMPLE_INT_WARM_OFFSET:
            new_setpoint = int(internal_temp) - SIMPLE_INT_SETPOINT_MILD
            fan = "medium"
        else:
            new_setpoint = int(internal_temp)
            fan = "low"

        current_sp = real_state.attributes.get("temperature") if real_state else None
        current_fan = real_state.attributes.get("fan_mode") if real_state else None
        try:
            current_sp = int(float(current_sp)) if current_sp is not None else None
        except (TypeError, ValueError):
            current_sp = None

        if current_sp != new_setpoint:
            await self.hass.services.async_call("climate", "set_temperature", {"entity_id": self._climate_entity, "temperature": new_setpoint}, blocking=True)
        if current_fan != fan:
            await self.hass.services.async_call("climate", "set_fan_mode", {"entity_id": self._climate_entity, "fan_mode": fan}, blocking=True)

    async def _async_thermal_simple_external(
        self, temp: float, target: float, internal_temp: float | None, real_state, dry_enabled: bool
    ) -> None:
        """Logica termica con sonda esterna (decimali).

        Senza dry:
          Accende in COOL se temp > target + 1.5
        Con dry:
          Accende in DRY se temp > target + 0.3, passa a COOL se temp > target + 1.5
          oppure dopo dry_max_min minuti in dry

        Spegne se temp <= target - 0.3 per 15 min consecutivi.
        """
        dry_max_min = int(get_conf(self.entry, CONF_SIMPLE_DRY_MAX_MIN, DEFAULT_SIMPLE_DRY_MAX_MIN))
        now = dt_util.utcnow()
        current_mode = real_state.state if real_state else "off"
        shutoff_threshold = target + SIMPLE_EXT_SHUTOFF_OFFSET  # target - 0.3
        is_on = self.hvac_mode == HVACMode.COOL or current_mode == "dry"

        # --- Spegnimento per target raggiunto ---
        if is_on:
            if temp <= shutoff_threshold:
                if self._simple_shutoff_since is None:
                    self._simple_shutoff_since = now
                elif (now - self._simple_shutoff_since) >= timedelta(minutes=SIMPLE_EXT_SHUTOFF_MIN):
                    _LOGGER.info("%s: [semplificato] spegnimento target raggiunto (ext, temp=%.1f)", self._attr_name, temp)
                    await self.hass.services.async_call("climate", "turn_off", {"entity_id": self._climate_entity}, blocking=True)
                    self._simple_shutoff_since = None
                    self._simple_dry_since = None
                    self._simple_night_auto_on = False
                    self._fv_auto_on = False
                    await self._async_simple_notify_ac_off(temp, target)
                    return
            else:
                self._simple_shutoff_since = None

        # --- Passaggio da DRY a COOL ---
        if dry_enabled and current_mode == "dry":
            dry_elapsed = (now - self._simple_dry_since) if self._simple_dry_since else timedelta(0)
            should_switch_cool = (
                temp > target + SIMPLE_EXT_DRY_HIGH or
                dry_elapsed >= timedelta(minutes=dry_max_min)
            )
            if should_switch_cool:
                _LOGGER.info("%s: [semplificato] DRY→COOL (ext, temp=%.1f, elapsed=%s)", self._attr_name, temp, dry_elapsed)
                await self.hass.services.async_call("climate", "turn_on", {"entity_id": self._climate_entity}, blocking=True)
                self._simple_dry_since = None
            else:
                _LOGGER.debug("%s: [semplificato] in DRY (ext, temp=%.1f, elapsed=%s)", self._attr_name, temp, dry_elapsed)
                return  # rimane in dry

        # --- Accensione ---
        if not is_on:
            if dry_enabled and temp > target + SIMPLE_EXT_DRY_LOW and temp <= target + SIMPLE_EXT_DRY_HIGH:
                _LOGGER.info("%s: [semplificato] accensione DRY (ext, temp=%.1f)", self._attr_name, temp)
                await self.hass.services.async_call("climate", "set_hvac_mode", {"entity_id": self._climate_entity, "hvac_mode": "dry"}, blocking=True)
                self._simple_dry_since = now
                self._simple_night_auto_on = self._simple_is_night()
                self._fv_auto_on = False
                await self._async_simple_notify_ac_on(temp)
                return
            elif temp > target + SIMPLE_EXT_TURN_ON_OFFSET:
                _LOGGER.info("%s: [semplificato] accensione COOL diretta (ext, temp=%.1f)", self._attr_name, temp)
                await self.hass.services.async_call("climate", "turn_on", {"entity_id": self._climate_entity}, blocking=True)
                self._simple_dry_since = None
                self._simple_night_auto_on = self._simple_is_night()
                self._fv_auto_on = False
                await self._async_simple_notify_ac_on(temp)
            return

        # --- Regolazione termica (clima in COOL) ---
        if internal_temp is None:
            return

        if temp > target + SIMPLE_EXT_HOT_OFFSET:
            new_setpoint = internal_temp - SIMPLE_EXT_SETPOINT_HOT
            fan = "high"
        elif temp > target + SIMPLE_EXT_WARM_OFFSET:
            new_setpoint = internal_temp - SIMPLE_EXT_SETPOINT_HOT
            fan = "medium"
        elif temp > target + SIMPLE_EXT_MILD_OFFSET:
            new_setpoint = internal_temp - SIMPLE_EXT_SETPOINT_MILD
            fan = "low"
        else:
            new_setpoint = internal_temp
            fan = "low"

        new_setpoint_r = self._round_setpoint(new_setpoint)
        current_sp = real_state.attributes.get("temperature") if real_state else None
        current_fan = real_state.attributes.get("fan_mode") if real_state else None
        try:
            current_sp_r = self._round_setpoint(float(current_sp)) if current_sp is not None else None
        except (TypeError, ValueError):
            current_sp_r = None

        if current_sp_r != new_setpoint_r:
            await self.hass.services.async_call("climate", "set_temperature", {"entity_id": self._climate_entity, "temperature": new_setpoint_r}, blocking=True)
        if current_fan != fan:
            await self.hass.services.async_call("climate", "set_fan_mode", {"entity_id": self._climate_entity, "fan_mode": fan}, blocking=True)

    async def _async_handle_fv_turn_on_simple(self, temp: float, target: float) -> None:
        """Accensione FV per il modo semplificato."""
        if self.hvac_mode != HVACMode.OFF:
            return
        if not (self._fv_sensor and self._consumption_sensor and self._battery_sensor):
            return
        fv = self._read_float(self._fv_sensor)
        consumo = self._read_float(self._consumption_sensor)
        soc = self._read_float(self._battery_sensor)
        if fv is None or consumo is None or soc is None:
            return
        margin = float(get_conf(self.entry, CONF_FV_MARGIN_W, DEFAULT_FV_MARGIN_W))
        soc_min = float(get_conf(self.entry, CONF_SOC_MIN, DEFAULT_SOC_MIN))
        turn_on_offset = float(get_conf(self.entry, CONF_TURN_ON_OFFSET, DEFAULT_TURN_ON_OFFSET))
        if not (fv > consumo + margin and soc > soc_min and temp > target + turn_on_offset):
            return
        coord = self.hass.data.setdefault(DOMAIN, {}).setdefault("_coordination", {})
        stagger_min = float(get_conf(self.entry, CONF_FV_STAGGER_MIN, DEFAULT_FV_STAGGER_MIN))
        last_on = coord.get("last_fv_turn_on")
        if last_on is not None and (dt_util.utcnow() - last_on) < timedelta(minutes=stagger_min):
            return
        _LOGGER.info("%s: [semplificato FV] accensione da fotovoltaico (fv=%.0fW, consumo=%.0fW)", self._attr_name, fv, consumo)
        await self.hass.services.async_call("climate", "turn_on", {"entity_id": self._climate_entity}, blocking=True)
        coord["last_fv_turn_on"] = dt_util.utcnow()
        self._fv_auto_on = True
        self._simple_night_auto_on = False
        await self._async_simple_notify_ac_on(temp)

    # ------------------------------------------------------------------
    # Notifiche modo semplificato
    # ------------------------------------------------------------------

    async def _async_simple_speak(self, message: str) -> None:
        """TTS per modo semplificato — silenzia di notte se configurato."""
        players = get_conf(self.entry, CONF_TTS_PLAYERS, [])
        if not players:
            return
        if self._simple_is_quiet_night() and bool(get_conf(self.entry, CONF_SIMPLE_QUIET_NIGHT_TTS, DEFAULT_SIMPLE_QUIET_NIGHT_TTS)):
            _LOGGER.debug("%s: [semplificato] TTS soppresso (notte)", self._attr_name)
            return
        engine = get_conf(self.entry, CONF_TTS_ENGINE)
        if not engine:
            tts_states = self.hass.states.async_all("tts")
            if not tts_states:
                return
            engine = tts_states[0].entity_id
        await self.hass.services.async_call(
            "tts", "speak",
            {"entity_id": engine, "media_player_entity_id": players, "message": message, "cache": True},
            blocking=True,
        )

    async def _async_simple_notify(self, message: str, bypass_quiet: bool = False) -> None:
        """Notifica Telegram per modo semplificato — silenzia di notte se configurato."""
        targets = get_conf(self.entry, CONF_NOTIFY_TARGETS, [])
        chat_ids = get_conf(self.entry, CONF_NOTIFY_CHAT_IDS)
        if not targets and not chat_ids:
            return
        if not bypass_quiet and self._simple_is_quiet_night() and bool(get_conf(self.entry, CONF_SIMPLE_QUIET_NIGHT_NOTIFY, DEFAULT_SIMPLE_QUIET_NIGHT_NOTIFY)):
            _LOGGER.debug("%s: [semplificato] notifica soppressa (notte)", self._attr_name)
            return
        if targets:
            await self.hass.services.async_call("notify", "send_message", {"entity_id": targets, "message": message}, blocking=True)
        elif chat_ids:
            ids = [c.strip() for c in str(chat_ids).split(",") if c.strip()]
            await self.hass.services.async_call("telegram_bot", "send_message", {"target": ids, "message": message}, blocking=True)

    async def _async_handle_fv_shutoff_simple(self, temp: float, target: float) -> None:
        """Spegnimento FV per il modo semplificato con sliding window.

        4 casi:
        1. Acceso di notte automaticamente (_simple_night_auto_on) → non spegnere mai per FV
        2. Acceso dal FV (_fv_auto_on) → spegne sempre se FV insufficiente
        3. Acceso manualmente E siamo prima di tramonto-Xh → spegne se FV insufficiente
        4. Acceso manualmente dopo tramonto-Xh → non toccare
        """
        if not (self._fv_sensor and self._consumption_sensor):
            return

        current_mode = self.hass.states.get(self._climate_entity)
        is_on = self.hvac_mode == HVACMode.COOL or (
            current_mode and current_mode.state == "dry"
        )
        if not is_on:
            self._fv_surplus_buffer = []
            return

        # Caso 1: acceso dalla modalità notturna → FV non interviene mai
        if self._simple_night_auto_on:
            self._fv_surplus_buffer = []
            return

        # Caso 2: acceso dal FV → può sempre spegnere
        # Caso 3: acceso manualmente ma siamo nella finestra di controllo → può spegnere
        # Caso 4: acceso manualmente fuori finestra → non toccare
        if not self._fv_auto_on and not self._simple_can_control_manual():
            self._fv_surplus_buffer = []
            return

        # Sliding window
        fv = self._read_float(self._fv_sensor)
        consumo = self._read_float(self._consumption_sensor)
        if fv is None or consumo is None:
            return

        surplus = fv - consumo
        threshold = float(get_conf(self.entry, CONF_FV_SHUTOFF_THRESHOLD, DEFAULT_FV_SHUTOFF_THRESHOLD))
        delay_min = int(get_conf(self.entry, CONF_FV_SHUTOFF_DELAY_MIN, DEFAULT_FV_SHUTOFF_DELAY_MIN))

        self._fv_surplus_buffer.append(surplus)
        if len(self._fv_surplus_buffer) > delay_min:
            self._fv_surplus_buffer.pop(0)

        _LOGGER.debug(
            "%s: [semplificato FV] shutoff buffer %s (soglia=%.0f, fv_auto=%s, manual_ctrl=%s)",
            self._attr_name, [round(s) for s in self._fv_surplus_buffer],
            threshold, self._fv_auto_on, self._simple_can_control_manual(),
        )

        if len(self._fv_surplus_buffer) < delay_min:
            return
        if not all(s < threshold for s in self._fv_surplus_buffer):
            return

        # Coordinamento cascata
        now = dt_util.utcnow()
        coord = self.hass.data.setdefault(DOMAIN, {}).setdefault("_coordination", {})
        stagger_min = float(get_conf(self.entry, CONF_FV_STAGGER_MIN, DEFAULT_FV_STAGGER_MIN))
        last_off = coord.get("last_fv_shutoff")
        if last_off is not None and (now - last_off) < timedelta(minutes=stagger_min):
            return

        _LOGGER.info(
            "%s: [semplificato FV] spegnimento (fv=%.0fW, consumo=%.0fW, fv_auto=%s)",
            self._attr_name, fv, consumo, self._fv_auto_on,
        )
        await self.hass.services.async_call("climate", "turn_off", {"entity_id": self._climate_entity}, blocking=True)
        coord["last_fv_shutoff"] = now
        self._fv_surplus_buffer = []
        self._fv_auto_on = False
        await self._async_simple_notify_ac_off(temp, target)
        if not bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_AC_ON, DEFAULT_SIMPLE_NOTIFY_AC_ON)):
            return
        msg = await self._async_render(DEFAULT_SIMPLE_MSG_AC_ON, {"name": self._attr_name, "temp": round(temp, 1)})
        await self._async_simple_speak(msg)
        await self._async_simple_notify(msg)

    async def _async_simple_notify_ac_off(self, temp: float, target: float) -> None:
        if not bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_AC_OFF, DEFAULT_SIMPLE_NOTIFY_AC_OFF)):
            return
        msg = await self._async_render(DEFAULT_SIMPLE_MSG_AC_OFF, {"name": self._attr_name, "temp": round(temp, 1), "target": round(target, 1)})
        await self._async_simple_speak(msg)
        await self._async_simple_notify(msg)

    async def _async_simple_notify_night_start(self, target: float) -> None:
        if not bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_NIGHT_START, DEFAULT_SIMPLE_NOTIFY_NIGHT_START)):
            return
        msg = await self._async_render(DEFAULT_SIMPLE_MSG_NIGHT_START, {"name": self._attr_name, "target": round(target, 1)})
        await self._async_simple_speak(msg)
        await self._async_simple_notify(msg, bypass_quiet=True)

    async def _async_simple_notify_night_end(self) -> None:
        if not bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_NIGHT_END, DEFAULT_SIMPLE_NOTIFY_NIGHT_END)):
            return
        msg = await self._async_render(DEFAULT_SIMPLE_MSG_NIGHT_END, {"name": self._attr_name})
        await self._async_simple_speak(msg)
        await self._async_simple_notify(msg, bypass_quiet=True)

    async def _async_simple_notify_door(self, is_open: bool) -> None:
        key = CONF_SIMPLE_NOTIFY_DOOR_OPEN if is_open else CONF_SIMPLE_NOTIFY_DOOR_CLOSE
        default = DEFAULT_SIMPLE_NOTIFY_DOOR_OPEN if is_open else DEFAULT_SIMPLE_NOTIFY_DOOR_CLOSE
        if not bool(get_conf(self.entry, key, default)):
            return
        tpl = DEFAULT_SIMPLE_MSG_DOOR_OPEN if is_open else DEFAULT_SIMPLE_MSG_DOOR_CLOSE
        msg = await self._async_render(tpl, {"name": self._attr_name})
        await self._async_simple_speak(msg)
        await self._async_simple_notify(msg)

    async def _async_simple_notify_window(self, is_open: bool, delay_min: int = 0) -> None:
        key = CONF_SIMPLE_NOTIFY_WINDOW_OPEN if is_open else CONF_SIMPLE_NOTIFY_WINDOW_CLOSE
        default = DEFAULT_SIMPLE_NOTIFY_WINDOW_OPEN if is_open else DEFAULT_SIMPLE_NOTIFY_WINDOW_CLOSE
        if not bool(get_conf(self.entry, key, default)):
            return
        tpl = DEFAULT_SIMPLE_MSG_WINDOW_OPEN if is_open else DEFAULT_SIMPLE_MSG_WINDOW_CLOSE
        msg = await self._async_render(tpl, {"name": self._attr_name, "delay": delay_min})
        await self._async_simple_speak(msg)
        await self._async_simple_notify(msg)

    # ------------------------------------------------------------------
    # Helpers orari / stato
    # ------------------------------------------------------------------

    def _effective_target(self) -> float:
        target = self._target_temperature
        if self._is_night_mode_active():
            target += float(get_conf(self.entry, CONF_NIGHT_OFFSET, DEFAULT_NIGHT_OFFSET))
        return target

    def _is_night_mode_active(self) -> bool:
        return self._in_time_window(
            get_conf(self.entry, CONF_NIGHT_START_TIME, DEFAULT_NIGHT_START_TIME),
            get_conf(self.entry, CONF_NIGHT_END_TIME, DEFAULT_NIGHT_END_TIME),
        )

    def _within_fv_window(self) -> bool:
        return self._in_time_window(
            get_conf(self.entry, CONF_FV_START_TIME, DEFAULT_FV_START_TIME),
            get_conf(self.entry, CONF_FV_END_TIME, DEFAULT_FV_END_TIME),
        )

    def _within_fv_shutoff_window(self) -> bool:
        start_str = get_conf(self.entry, CONF_FV_START_TIME, DEFAULT_FV_START_TIME)
        end_str = get_conf(self.entry, CONF_FV_END_TIME, DEFAULT_FV_END_TIME)
        extra_h = float(get_conf(self.entry, CONF_FV_SHUTOFF_EXTRA_HOURS, DEFAULT_FV_SHUTOFF_EXTRA_HOURS))
        try:
            start = dt_time.fromisoformat(str(start_str))
            end_base = dt_time.fromisoformat(str(end_str))
        except ValueError:
            return True
        dummy_date = datetime(2000, 1, 1)
        end_dt = datetime.combine(dummy_date, end_base) + timedelta(hours=extra_h)
        end_extended = dt_time(23, 59, 59) if end_dt.date() > dummy_date.date() else end_dt.time()
        now_t = dt_util.now().time()
        if start <= end_extended:
            return start <= now_t <= end_extended
        return now_t >= start or now_t <= end_extended

    def _is_quiet_time(self) -> bool:
        if not bool(get_conf(self.entry, CONF_QUIET_ENABLED, DEFAULT_QUIET_ENABLED)):
            return False
        return self._in_time_window(
            get_conf(self.entry, CONF_QUIET_START_TIME, DEFAULT_QUIET_START_TIME),
            get_conf(self.entry, CONF_QUIET_END_TIME, DEFAULT_QUIET_END_TIME),
        )

    @staticmethod
    def _in_time_window(start_str: str, end_str: str) -> bool:
        try:
            start = dt_time.fromisoformat(str(start_str))
            end = dt_time.fromisoformat(str(end_str))
        except ValueError:
            return False
        if start == end:
            return False
        now_t = dt_util.now().time()
        if start <= end:
            return start <= now_t <= end
        return now_t >= start or now_t <= end

    def _is_window_open(self) -> bool:
        if not self._window_sensor:
            return False
        state = self.hass.states.get(self._window_sensor)
        if state is None or state.state in _INVALID_STATES:
            return False
        return state.state == "on"

    def _is_door_open(self) -> bool:
        if not self._door_sensor:
            return False
        state = self.hass.states.get(self._door_sensor)
        if state is None or state.state in _INVALID_STATES:
            return False
        return state.state == "on"

    def _switch_state(self, key: str, default: bool) -> bool:
        data = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {})
        switch = data.get(key)
        if switch is None:
            return default
        return bool(getattr(switch, "is_on", default))

    def _read_float(self, entity_id: str | None) -> float | None:
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None:
            return None
        try:
            return float(state.state)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _round_setpoint(value: float) -> int:
        floor_val = math.floor(value)
        return int(floor_val) if value - floor_val <= 0.5 else int(floor_val) + 1

    @staticmethod
    def _is_real_transition(old_state: State | None, new_state: State | None, from_val: str, to_val: str) -> bool:
        """Verifica transizione esatta from_val→to_val, ignorando unavailable/unknown."""
        if new_state is None or old_state is None:
            return False
        if old_state.state in _INVALID_STATES or new_state.state in _INVALID_STATES:
            return False
        return old_state.state == from_val and new_state.state == to_val

    # ------------------------------------------------------------------
    # Accensione da FV
    # ------------------------------------------------------------------

    async def _async_handle_fv_turn_on(self, temp: float, target: float) -> None:
        if not self._fv_basic_eligible(temp, target):
            return
        coord = self.hass.data.setdefault(DOMAIN, {}).setdefault("_coordination", {})
        stagger_min = float(get_conf(self.entry, CONF_FV_STAGGER_MIN, DEFAULT_FV_STAGGER_MIN))
        last_on = coord.get("last_fv_turn_on")
        if last_on is not None and (dt_util.utcnow() - last_on) < timedelta(minutes=stagger_min):
            return
        my_priority = (float(get_conf(self.entry, CONF_FV_PRIORITY, DEFAULT_FV_PRIORITY)), self.entry.entry_id)
        for entry_data in self.hass.data.get(DOMAIN, {}).values():
            if not isinstance(entry_data, dict):
                continue
            sibling = entry_data.get("climate")
            if sibling is None or sibling is self:
                continue
            if not sibling._fv_basic_eligible(sibling.current_temperature, sibling._effective_target()):
                continue
            sib_priority = (float(get_conf(sibling.entry, CONF_FV_PRIORITY, DEFAULT_FV_PRIORITY)), sibling.entry.entry_id)
            if sib_priority < my_priority:
                return
        fv = self._read_float(self._fv_sensor) or 0
        await self.hass.services.async_call("climate", "turn_on", {"entity_id": self._climate_entity}, blocking=True)
        coord["last_fv_turn_on"] = dt_util.utcnow()
        await self._async_notify_power_event(
            reason=REASON_FV, is_on=True,
            extra={"fv": round(fv), "temp": round(temp, 1), "target": round(target, 1)},
        )

    def _fv_basic_eligible(self, temp: float | None, target: float) -> bool:
        if not (self._fv_sensor and self._consumption_sensor and self._battery_sensor):
            return False
        if self.hvac_mode != HVACMode.OFF or temp is None:
            return False
        fv = self._read_float(self._fv_sensor)
        consumo = self._read_float(self._consumption_sensor)
        soc = self._read_float(self._battery_sensor)
        if fv is None or consumo is None or soc is None:
            return False
        margin = float(get_conf(self.entry, CONF_FV_MARGIN_W, DEFAULT_FV_MARGIN_W))
        soc_min = float(get_conf(self.entry, CONF_SOC_MIN, DEFAULT_SOC_MIN))
        turn_on_offset = float(get_conf(self.entry, CONF_TURN_ON_OFFSET, DEFAULT_TURN_ON_OFFSET))
        return fv > consumo + margin and soc > soc_min and temp > target + turn_on_offset

    # ------------------------------------------------------------------
    # Accensione notturna
    # ------------------------------------------------------------------

    async def _async_handle_night_turn_on(self, temp: float, target: float) -> None:
        if self.hvac_mode != HVACMode.OFF or temp is None:
            return
        night_turn_on_offset = float(get_conf(self.entry, CONF_NIGHT_TURN_ON_OFFSET, DEFAULT_NIGHT_TURN_ON_OFFSET))
        if temp <= target + night_turn_on_offset:
            return
        _LOGGER.debug("%s: accensione notturna (temp=%.1f)", self._attr_name, temp)
        await self.hass.services.async_call("climate", "turn_on", {"entity_id": self._climate_entity}, blocking=True)
        self._night_auto_on = True  # segnala che è stato acceso automaticamente di notte
        await self._async_notify_power_event(
            reason=REASON_NIGHT, is_on=True,
            extra={"temp": round(temp, 1), "target": round(target, 1)},
        )

    # ------------------------------------------------------------------
    # Spegnimento diurno FV — sliding window
    # ------------------------------------------------------------------

    async def _async_handle_fv_shutoff(self, temp: float, target: float) -> None:
        if not self._within_fv_shutoff_window():
            self._fv_surplus_buffer = []
            return
        if not (self._fv_sensor and self._consumption_sensor):
            return
        if self.hvac_mode == HVACMode.OFF:
            self._fv_surplus_buffer = []
            return
        fv = self._read_float(self._fv_sensor)
        consumo = self._read_float(self._consumption_sensor)
        if fv is None or consumo is None:
            return
        surplus = fv - consumo
        threshold = float(get_conf(self.entry, CONF_FV_SHUTOFF_THRESHOLD, DEFAULT_FV_SHUTOFF_THRESHOLD))
        delay_min = int(get_conf(self.entry, CONF_FV_SHUTOFF_DELAY_MIN, DEFAULT_FV_SHUTOFF_DELAY_MIN))
        self._fv_surplus_buffer.append(surplus)
        if len(self._fv_surplus_buffer) > delay_min:
            self._fv_surplus_buffer.pop(0)
        _LOGGER.debug(
            "%s: FV shutoff buffer %s (soglia=%.0f, necessari=%d)",
            self._attr_name, [round(s) for s in self._fv_surplus_buffer], threshold, delay_min,
        )
        if len(self._fv_surplus_buffer) < delay_min:
            return
        if not all(s < threshold for s in self._fv_surplus_buffer):
            return
        now = dt_util.utcnow()
        coord = self.hass.data.setdefault(DOMAIN, {}).setdefault("_coordination", {})
        stagger_min = float(get_conf(self.entry, CONF_FV_STAGGER_MIN, DEFAULT_FV_STAGGER_MIN))
        last_off = coord.get("last_fv_shutoff")
        if last_off is not None and (now - last_off) < timedelta(minutes=stagger_min):
            return
        my_priority = (float(get_conf(self.entry, CONF_FV_PRIORITY, DEFAULT_FV_PRIORITY)), self.entry.entry_id)
        for entry_data in self.hass.data.get(DOMAIN, {}).values():
            if not isinstance(entry_data, dict):
                continue
            sibling = entry_data.get("climate")
            if sibling is None or sibling is self or sibling.hvac_mode == HVACMode.OFF:
                continue
            sib_priority = (float(get_conf(sibling.entry, CONF_FV_PRIORITY, DEFAULT_FV_PRIORITY)), sibling.entry.entry_id)
            if sib_priority > my_priority:
                return
        _LOGGER.info(
            "%s: spegnimento FV (buffer=%s, soglia=%.0fW)",
            self._attr_name, [round(s) for s in self._fv_surplus_buffer], threshold,
        )
        await self.hass.services.async_call("climate", "turn_off", {"entity_id": self._climate_entity}, blocking=True)
        coord["last_fv_shutoff"] = now
        self._fv_surplus_buffer = []
        await self._async_notify_power_event(
            reason=REASON_FV_SHUTOFF, is_on=False,
            extra={"fv": round(fv), "consumo": round(consumo)},
        )

    # ------------------------------------------------------------------
    # Spegnimento notturno per target raggiunto
    # ------------------------------------------------------------------

    async def _async_handle_night_shutoff(self, temp: float, target: float) -> None:
        if self.hvac_mode == HVACMode.OFF:
            self._night_below_since = None
            return
        shutoff_delta = float(get_conf(self.entry, CONF_NIGHT_SHUTOFF_DELTA, DEFAULT_NIGHT_SHUTOFF_DELTA))
        shutoff_min = int(get_conf(self.entry, CONF_NIGHT_SHUTOFF_MIN, DEFAULT_NIGHT_SHUTOFF_MIN))
        threshold = target + shutoff_delta
        if temp > threshold:
            self._night_below_since = None
            return
        now = dt_util.utcnow()
        if self._night_below_since is None:
            self._night_below_since = now
            return
        if (now - self._night_below_since) < timedelta(minutes=shutoff_min):
            return
        _LOGGER.info("%s: spegnimento notturno target (temp=%.1f ≤ %.1f)", self._attr_name, temp, threshold)
        await self.hass.services.async_call("climate", "turn_off", {"entity_id": self._climate_entity}, blocking=True)
        self._night_below_since = None
        self._night_auto_on = False
        await self._async_notify_power_event(
            reason=REASON_NIGHT_SHUTOFF, is_on=False,
            extra={"temp": round(temp, 1), "target": round(target, 1)},
        )

    # ------------------------------------------------------------------
    # Spegnimento a fine modalità notturna
    # ------------------------------------------------------------------

    async def _async_handle_night_end_shutoff(self) -> None:
        """Chiamato una volta al ciclo in cui la modalità notturna termina.

        Logica:
        - Se night_end_shutoff_enabled=True → spegne sempre (se clima è acceso)
        - Se night_end_shutoff_auto_only=True → spegne solo se _night_auto_on è True
        - I due flag sono indipendenti: entrambi possono essere attivi,
          nel qual caso il "sempre" ha precedenza.
        """
        shutoff_always = bool(get_conf(self.entry, CONF_NIGHT_END_SHUTOFF_ENABLED, DEFAULT_NIGHT_END_SHUTOFF_ENABLED))
        shutoff_auto_only = bool(get_conf(self.entry, CONF_NIGHT_END_SHUTOFF_AUTO_ONLY, DEFAULT_NIGHT_END_SHUTOFF_AUTO_ONLY))

        if not shutoff_always and not shutoff_auto_only:
            return  # nessuno dei due abilitato

        if self.hvac_mode == HVACMode.OFF:
            self._night_auto_on = False
            return  # clima già spento, niente da fare

        should_shutoff = shutoff_always or (shutoff_auto_only and self._night_auto_on)

        if not should_shutoff:
            # auto_only attivo ma il clima non era stato acceso automaticamente
            _LOGGER.debug(
                "%s: fine notte — spegnimento auto_only attivo ma clima non era acceso automaticamente, skip",
                self._attr_name,
            )
            return

        _LOGGER.info("%s: spegnimento fine modalità notturna (auto_on=%s)", self._attr_name, self._night_auto_on)
        await self.hass.services.async_call("climate", "turn_off", {"entity_id": self._climate_entity}, blocking=True)
        self._night_auto_on = False
        self._night_below_since = None

        # Notifica dedicata (canali separati configurabili)
        await self._async_notify_night_end_shutoff()

    # ------------------------------------------------------------------
    # Regolazione termica
    # ------------------------------------------------------------------

    async def _async_handle_thermal(self, temp: float, target: float) -> None:
        if self.hvac_mode == HVACMode.OFF:
            return
        extreme_offset = float(get_conf(self.entry, CONF_EXTREME_OFFSET, DEFAULT_EXTREME_OFFSET))
        hot_offset = float(get_conf(self.entry, CONF_HOT_OFFSET, DEFAULT_HOT_OFFSET))
        range_offset = float(get_conf(self.entry, CONF_RANGE_OFFSET, DEFAULT_RANGE_OFFSET))
        below_offset = float(get_conf(self.entry, CONF_BELOW_OFFSET, DEFAULT_BELOW_OFFSET))
        delta = float(get_conf(self.entry, CONF_TEMP_DELTA, DEFAULT_TEMP_DELTA))
        extreme_delta = float(get_conf(self.entry, CONF_EXTREME_DELTA, DEFAULT_EXTREME_DELTA))
        if temp > target + extreme_offset:
            new_temp, fan_mode = target - extreme_delta, "high"
        elif temp > target + hot_offset:
            new_temp, fan_mode = target - delta, "medium"
        elif temp > target + range_offset:
            new_temp, fan_mode = target - delta, "low"
        elif temp > target - below_offset:
            new_temp, fan_mode = target, "low"
        else:
            new_temp, fan_mode = target + delta, "low"
        if self._switch_state(SWITCH_KEY_QUICK, False) and temp > target + range_offset:
            new_temp -= 1.0
            fan_mode = "high"
        real_state = self.hass.states.get(self._climate_entity)
        current_temp = real_state.attributes.get("temperature") if real_state else None
        current_fan = real_state.attributes.get("fan_mode") if real_state else None
        internal_temp_raw = real_state.attributes.get("current_temperature") if real_state else None
        internal_temp_value: float | None = None
        if internal_temp_raw is not None:
            try:
                internal_temp_value = float(internal_temp_raw)
            except (TypeError, ValueError):
                pass
        if internal_temp_value is not None:
            calib_raw = temp - internal_temp_value
            if calib_raw > 0:
                gap = max(0.0, temp - target)
                fraction = min(gap / extreme_offset, 1.0) if extreme_offset > 0 else (1.0 if gap > 0 else 0.0)
                calib_scaled = min(calib_raw * fraction, float(get_conf(self.entry, CONF_CALIBRATION_MAX_OFFSET, DEFAULT_CALIBRATION_MAX_OFFSET)))
                new_temp -= calib_scaled
        new_temp_rounded = self._round_setpoint(new_temp)
        if internal_temp_value is not None and temp > target + range_offset:
            min_gap = float(get_conf(self.entry, CONF_MIN_BELOW_INTERNAL, DEFAULT_MIN_BELOW_INTERNAL))
            max_allowed = math.floor(internal_temp_value - min_gap)
            if new_temp_rounded > max_allowed:
                new_temp_rounded = int(max_allowed)
        current_temp_rounded: int | None = None
        if current_temp is not None:
            try:
                current_temp_rounded = self._round_setpoint(float(current_temp))
            except (TypeError, ValueError):
                pass
        if current_temp_rounded is None or current_temp_rounded != new_temp_rounded:
            await self.hass.services.async_call("climate", "set_temperature", {"entity_id": self._climate_entity, "temperature": new_temp_rounded}, blocking=True)
            await self._async_notify_temp_change(current_temp_rounded, new_temp_rounded, fan_mode, temp, target)
        if current_fan != fan_mode:
            await self.hass.services.async_call("climate", "set_fan_mode", {"entity_id": self._climate_entity, "fan_mode": fan_mode}, blocking=True)

    # ------------------------------------------------------------------
    # Boost presenza
    # ------------------------------------------------------------------

    async def _async_handle_presence_boost(self, temp: float, target: float) -> None:
        if self.hvac_mode != HVACMode.COOL or not self._presence_sensor or self._presence_since is None:
            return
        if not bool(get_conf(self.entry, CONF_PRESENCE_BOOST_ENABLED, DEFAULT_PRESENCE_BOOST_ENABLED)):
            return
        boost_minutes = int(get_conf(self.entry, CONF_PRESENCE_BOOST_MIN, DEFAULT_PRESENCE_BOOST_MIN))
        boost_offset = float(get_conf(self.entry, CONF_PRESENCE_BOOST_OFFSET, DEFAULT_PRESENCE_BOOST_OFFSET))
        elapsed = dt_util.utcnow() - self._presence_since
        if elapsed >= timedelta(minutes=boost_minutes) and temp > target + boost_offset and self.fan_mode != "medium":
            await self.hass.services.async_call("climate", "set_fan_mode", {"entity_id": self._climate_entity, "fan_mode": "medium"}, blocking=True)

    # ------------------------------------------------------------------
    # Gestione finestra
    # ------------------------------------------------------------------

    async def _async_handle_window(self, new_state: State | None, old_state: State | None) -> None:
        if new_state is None:
            return
        mode = get_conf(self.entry, CONF_CONFIG_MODE, CONFIG_MODE_FULL)
        is_simple = mode in (CONFIG_MODE_SIMPLE, CONFIG_MODE_SIMPLE_FV)

        if self._is_real_transition(old_state, new_state, "off", "on"):
            if self._window_cancel_timer is not None:
                self._window_cancel_timer()
                self._window_cancel_timer = None
            if is_simple:
                await self._async_simple_notify_window(True, SIMPLE_WINDOW_DELAY_MIN)
                await self._async_window_opened_simple()
            else:
                await self._async_window_opened()
        elif self._is_real_transition(old_state, new_state, "on", "off"):
            if self._window_cancel_timer is not None:
                self._window_cancel_timer()
                self._window_cancel_timer = None
            if is_simple:
                await self._async_simple_notify_window(False)
                await self._async_window_closed()
            else:
                await self._async_window_closed()

    async def _async_window_opened_simple(self) -> None:
        """Apertura finestra in modo semplificato — delay fisso 5 minuti."""
        if self.hvac_mode != HVACMode.COOL:
            return
        real_state = self.hass.states.get(self._climate_entity)
        if real_state is None:
            return
        self._snapshot = {
            "hvac_mode": real_state.state,
            "temperature": real_state.attributes.get("temperature"),
            "fan_mode": real_state.attributes.get("fan_mode"),
        }
        self._window_cancel_timer = async_call_later(
            self.hass, timedelta(minutes=SIMPLE_WINDOW_DELAY_MIN), self._async_window_timeout
        )

    async def _async_window_opened(self) -> None:
        if self.hvac_mode != HVACMode.COOL:
            return
        real_state = self.hass.states.get(self._climate_entity)
        if real_state is None:
            return
        self._snapshot = {
            "hvac_mode": real_state.state,
            "temperature": real_state.attributes.get("temperature"),
            "fan_mode": real_state.attributes.get("fan_mode"),
        }
        delay_min = int(get_conf(self.entry, CONF_WINDOW_DELAY_MIN, DEFAULT_WINDOW_DELAY_MIN))
        await self._async_notify_window_open_tts(delay_min)
        self._window_cancel_timer = async_call_later(self.hass, timedelta(minutes=delay_min), self._async_window_timeout)

    async def _async_window_timeout(self, now: datetime | None = None) -> None:
        self._window_cancel_timer = None
        if not self._is_window_open():
            return
        await self.hass.services.async_call("climate", "turn_off", {"entity_id": self._climate_entity}, blocking=True)
        await self._async_notify_window_closed_off()
        self.async_write_ha_state()

    async def _async_window_closed(self) -> None:
        await self._async_notify_window_closed()
        if self._snapshot is None:
            return
        snap, self._snapshot = self._snapshot, None
        if snap["hvac_mode"] == "off":
            return
        await self.hass.services.async_call("climate", "turn_on", {"entity_id": self._climate_entity}, blocking=True)
        if snap.get("temperature") is not None:
            await self.hass.services.async_call("climate", "set_temperature", {"entity_id": self._climate_entity, "temperature": snap["temperature"]}, blocking=True)
        if snap.get("fan_mode") is not None:
            await self.hass.services.async_call("climate", "set_fan_mode", {"entity_id": self._climate_entity, "fan_mode": snap["fan_mode"]}, blocking=True)

    # ------------------------------------------------------------------
    # Gestione porta
    # ------------------------------------------------------------------

    async def _async_handle_door(self, new_state: State | None, old_state: State | None) -> None:
        if new_state is None:
            return
        mode = get_conf(self.entry, CONF_CONFIG_MODE, CONFIG_MODE_FULL)
        is_simple = mode in (CONFIG_MODE_SIMPLE, CONFIG_MODE_SIMPLE_FV)

        if self._is_real_transition(old_state, new_state, "off", "on"):
            if is_simple:
                await self._async_simple_notify_door(True)
            else:
                if not bool(get_conf(self.entry, CONF_DOOR_ALERT_ENABLED, DEFAULT_DOOR_ALERT_ENABLED)):
                    return
                message = await self._async_render(DEFAULT_DOOR_ALERT_OPEN_MESSAGE, {"name": self._attr_name})
                if bool(get_conf(self.entry, CONF_DOOR_ALERT_TTS, DEFAULT_DOOR_ALERT_TTS)):
                    await self._async_speak(message, bypass_quiet=False)
                if bool(get_conf(self.entry, CONF_DOOR_ALERT_NOTIFY, DEFAULT_DOOR_ALERT_NOTIFY)):
                    await self._async_send_notification(message, bypass_quiet=False)

        elif self._is_real_transition(old_state, new_state, "on", "off"):
            if is_simple:
                await self._async_simple_notify_door(False)
            else:
                if not bool(get_conf(self.entry, CONF_DOOR_ALERT_ENABLED, DEFAULT_DOOR_ALERT_ENABLED)):
                    return
                message = await self._async_render(DEFAULT_DOOR_ALERT_CLOSED_MESSAGE, {"name": self._attr_name})
                if bool(get_conf(self.entry, CONF_DOOR_ALERT_TTS, DEFAULT_DOOR_ALERT_TTS)):
                    await self._async_speak(message, bypass_quiet=False)
                if bool(get_conf(self.entry, CONF_DOOR_ALERT_NOTIFY, DEFAULT_DOOR_ALERT_NOTIFY)):
                    await self._async_send_notification(message, bypass_quiet=False)

    # ------------------------------------------------------------------
    # Avvisi accensione / spegnimento automatico
    # ------------------------------------------------------------------

    async def _async_notify_power_event(
        self,
        reason: str,
        is_on: bool,
        extra: dict[str, Any] | None = None,
    ) -> None:
        power_tts = bool(get_conf(self.entry, CONF_NOTIFY_POWER_TTS, DEFAULT_NOTIFY_POWER_TTS))
        power_notify = bool(get_conf(self.entry, CONF_NOTIFY_POWER_NOTIFY, DEFAULT_NOTIFY_POWER_NOTIFY))
        if not power_tts and not power_notify:
            return
        if is_on and reason == REASON_FV:
            tpl = DEFAULT_POWER_ON_FV_MESSAGE
        elif is_on and reason == REASON_NIGHT:
            tpl = DEFAULT_POWER_ON_NIGHT_MESSAGE
        elif not is_on and reason == REASON_FV_SHUTOFF:
            tpl = DEFAULT_POWER_OFF_FV_MESSAGE
        elif not is_on and reason == REASON_NIGHT_SHUTOFF:
            tpl = DEFAULT_POWER_OFF_NIGHT_MESSAGE
        else:
            stato = "acceso" if is_on else "spento"
            tpl = f"{{{{ name }}}}: climatizzatore {stato} automaticamente"
        variables = {"name": self._attr_name, **(extra or {})}
        message = await self._async_render(tpl, variables)
        if power_tts:
            await self._async_speak(message, bypass_quiet=False)
        if power_notify:
            await self._async_send_notification(message, bypass_quiet=False)

    async def _async_notify_night_end_shutoff(self) -> None:
        """Notifica dedicata per lo spegnimento a fine modalità notturna.

        Usa canali separati (notify_night_end_tts e notify_night_end_notify)
        indipendenti dagli altri avvisi di accensione/spegnimento.
        """
        tts_enabled = bool(get_conf(self.entry, CONF_NOTIFY_NIGHT_END_TTS, DEFAULT_NOTIFY_NIGHT_END_TTS))
        notify_enabled = bool(get_conf(self.entry, CONF_NOTIFY_NIGHT_END_NOTIFY, DEFAULT_NOTIFY_NIGHT_END_NOTIFY))
        if not tts_enabled and not notify_enabled:
            return
        message = await self._async_render(DEFAULT_POWER_OFF_NIGHT_END_MESSAGE, {"name": self._attr_name})
        if tts_enabled:
            await self._async_speak(message, bypass_quiet=True)  # fine notte = di giorno, non serve bypass_quiet
        if notify_enabled:
            await self._async_send_notification(message, bypass_quiet=True)

    # ------------------------------------------------------------------
    # Notifiche (helper base)
    # ------------------------------------------------------------------

    async def _async_render(self, template_str: str, variables: dict[str, Any]) -> str:
        try:
            tpl = Template(template_str, self.hass)
            return tpl.async_render(variables=variables, parse_result=False)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("%s: errore rendering ('%s'): %s", self._attr_name, template_str, err)
            return template_str

    async def _async_speak(self, message: str, bypass_quiet: bool = False) -> None:
        players = get_conf(self.entry, CONF_TTS_PLAYERS, [])
        if not players:
            return
        if not bypass_quiet and self._is_quiet_time() and bool(get_conf(self.entry, CONF_QUIET_TTS, DEFAULT_QUIET_TTS)):
            _LOGGER.debug("%s: TTS soppresso (fascia silenzio)", self._attr_name)
            return
        engine = get_conf(self.entry, CONF_TTS_ENGINE)
        if not engine:
            tts_states = self.hass.states.async_all("tts")
            if not tts_states:
                _LOGGER.warning("%s: nessun motore TTS disponibile", self._attr_name)
                return
            engine = tts_states[0].entity_id
        await self.hass.services.async_call(
            "tts", "speak",
            {"entity_id": engine, "media_player_entity_id": players, "message": message, "cache": True},
            blocking=True,
        )

    async def _async_send_notification(self, message: str, bypass_quiet: bool = False) -> None:
        targets = get_conf(self.entry, CONF_NOTIFY_TARGETS, [])
        chat_ids = get_conf(self.entry, CONF_NOTIFY_CHAT_IDS)
        if not targets and not chat_ids:
            return
        if not bypass_quiet and self._is_quiet_time() and bool(get_conf(self.entry, CONF_QUIET_NOTIFY, DEFAULT_QUIET_NOTIFY)):
            _LOGGER.debug("%s: notifica soppressa (fascia silenzio)", self._attr_name)
            return
        if targets:
            await self.hass.services.async_call("notify", "send_message", {"entity_id": targets, "message": message}, blocking=True)
        elif chat_ids:
            ids = [c.strip() for c in str(chat_ids).split(",") if c.strip()]
            await self.hass.services.async_call("telegram_bot", "send_message", {"target": ids, "message": message}, blocking=True)

    async def _async_notify_window_open_tts(self, delay_min: int) -> None:
        variables = {"delay": delay_min, "name": self._attr_name, "target": self._target_temperature}
        tts_tpl = get_conf(self.entry, CONF_TTS_MESSAGE_OPEN, DEFAULT_TTS_MESSAGE_OPEN)
        tts_msg = await self._async_render(tts_tpl, variables)
        await self._async_speak(tts_msg, bypass_quiet=False)
        notify_msg = await self._async_render(DEFAULT_NOTIFY_MESSAGE_OPEN, variables)
        await self._async_send_notification(notify_msg, bypass_quiet=False)

    async def _async_notify_window_closed(self) -> None:
        variables = {"name": self._attr_name}
        tts_msg = await self._async_render(DEFAULT_TTS_MESSAGE_CLOSED, variables)
        await self._async_speak(tts_msg, bypass_quiet=False)
        notify_msg = await self._async_render(DEFAULT_NOTIFY_MESSAGE_CLOSED, variables)
        await self._async_send_notification(notify_msg, bypass_quiet=False)

    async def _async_notify_window_closed_off(self) -> None:
        variables = {"name": self._attr_name, "target": self._target_temperature}
        tts_msg = await self._async_render(
            "Attenzione: il climatizzatore della {{ name }} è stato spento "
            "perché la finestra è rimasta aperta troppo a lungo.",
            variables,
        )
        await self._async_speak(tts_msg, bypass_quiet=False)
        notify_msg = await self._async_render(
            "⚠️ {{ name }}: finestra rimasta aperta, climatizzatore spento.",
            variables,
        )
        await self._async_send_notification(notify_msg, bypass_quiet=False)

    async def _async_notify_temp_change(self, old_temp, new_temp, fan_mode, room_temp, target) -> None:
        if not bool(get_conf(self.entry, CONF_NOTIFY_TEMP_CHANGE_ENABLED, DEFAULT_NOTIFY_TEMP_CHANGE_ENABLED)):
            return
        # Limite frequenza notifiche cambio temperatura
        if bool(get_conf(self.entry, CONF_NOTIFY_TEMP_CHANGE_LIMIT_ENABLED, DEFAULT_NOTIFY_TEMP_CHANGE_LIMIT_ENABLED)):
            limit_min = int(get_conf(self.entry, CONF_NOTIFY_TEMP_CHANGE_LIMIT_MIN, DEFAULT_NOTIFY_TEMP_CHANGE_LIMIT_MIN))
            now = dt_util.utcnow()
            if self._last_temp_notify is not None and (now - self._last_temp_notify) < timedelta(minutes=limit_min):
                _LOGGER.debug(
                    "%s: notifica cambio temp soppressa (limite %d min, ultima %s)",
                    self._attr_name, limit_min, self._last_temp_notify.isoformat(),
                )
                return
            self._last_temp_notify = now
        message_tpl = get_conf(self.entry, CONF_NOTIFY_TEMP_CHANGE_MESSAGE, DEFAULT_NOTIFY_TEMP_CHANGE_MESSAGE)
        message = await self._async_render(message_tpl, {
            "name": self._attr_name,
            "old_temp": old_temp,
            "new_temp": new_temp,
            "fan_mode": fan_mode,
            "room_temp": round(room_temp, 1),
            "target": round(target, 1),
        })
        await self._async_send_notification(message, bypass_quiet=False)
