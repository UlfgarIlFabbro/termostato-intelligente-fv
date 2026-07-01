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
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_call_later,
    async_track_point_in_time,
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
    CONF_FV_SHUTOFF_MANUAL,
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
    DEFAULT_FV_SHUTOFF_MANUAL,
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
    CONF_EMERGENCY_HEAT_END_THRESHOLD,
    CONF_EMERGENCY_HEAT_THRESHOLD,
    CONF_EMERGENCY_MSG_OFF,
    CONF_EMERGENCY_MSG_ON,
    CONF_EMERGENCY_NOTIFY_TELEGRAM,
    CONF_EMERGENCY_NOTIFY_TTS,
    CONF_POWER_LIMIT_ENABLED,
    CONF_POWER_LIMIT_HYSTERESIS_W,
    CONF_POWER_LIMIT_MAX_W,
    CONF_POWER_LIMIT_MODE,
    CONF_POWER_LIMIT_MSG_OFF,
    CONF_POWER_LIMIT_MSG_ON,
    CONF_POWER_LIMIT_NOTIFY_TELEGRAM,
    CONF_POWER_LIMIT_NOTIFY_TTS,
    CONF_POWER_LIMIT_RESTORE_MIN,
    CONF_POWER_LIMIT_SENSOR,
    CONF_SIMPLE_NIGHT_END,
    CONF_SIMPLE_NIGHT_START,
    CONF_SIMPLE_SUNSET_ANTICIPATE_H,
    CONF_SIMPLE_NOTIFY_TEL_AC_OFF,
    CONF_SIMPLE_NOTIFY_TEL_AC_ON,
    CONF_SIMPLE_NOTIFY_TEL_DOOR_CLOSE,
    CONF_SIMPLE_NOTIFY_TEL_DOOR_OPEN,
    CONF_SIMPLE_NOTIFY_TEL_NIGHT_END,
    CONF_SIMPLE_NOTIFY_TEL_NIGHT_START,
    CONF_SIMPLE_NOTIFY_TEL_TEMP_CHANGE,
    CONF_SIMPLE_NOTIFY_TEL_WINDOW_CLOSE,
    CONF_SIMPLE_NOTIFY_TEL_WINDOW_OPEN,
    CONF_SIMPLE_NOTIFY_TTS_AC_OFF,
    CONF_SIMPLE_NOTIFY_TTS_AC_ON,
    CONF_SIMPLE_NOTIFY_TTS_DOOR_CLOSE,
    CONF_SIMPLE_NOTIFY_TTS_DOOR_OPEN,
    CONF_SIMPLE_NOTIFY_TTS_NIGHT_END,
    CONF_SIMPLE_NOTIFY_TTS_NIGHT_START,
    CONF_SIMPLE_NOTIFY_TTS_TEMP_CHANGE,
    CONF_SIMPLE_NOTIFY_TTS_WINDOW_CLOSE,
    CONF_SIMPLE_NOTIFY_TTS_WINDOW_OPEN,
    CONF_SIMPLE_QUIET_NIGHT_NOTIFY,
    CONF_SIMPLE_QUIET_NIGHT_TTS,
    CONF_SIMPLE_TARGET_DAY,
    CONF_SIMPLE_TARGET_NIGHT,
    CONF_SIMPLE_DRY_ENABLED,
    CONF_SIMPLE_DRY_MAX_MIN,
    CONF_SIMPLE_NO_AUTO_ON_NIGHT,
    CONF_SIMPLE_TURN_ON_OFFSET,
    CONF_SIMPLE_TURN_ON_OFFSET,
    CONFIG_MODE_FULL,
    CONFIG_MODE_SIMPLE,
    DEFAULT_EMERGENCY_HEAT_END_THRESHOLD,
    DEFAULT_EMERGENCY_HEAT_THRESHOLD,
    DEFAULT_EMERGENCY_MSG_OFF,
    DEFAULT_EMERGENCY_MSG_ON,
    DEFAULT_EMERGENCY_NOTIFY_TELEGRAM,
    DEFAULT_EMERGENCY_NOTIFY_TTS,
    DEFAULT_POWER_LIMIT_ENABLED,
    DEFAULT_POWER_LIMIT_HYSTERESIS_W,
    DEFAULT_POWER_LIMIT_MAX_W,
    DEFAULT_POWER_LIMIT_MODE,
    DEFAULT_POWER_LIMIT_MSG_OFF,
    DEFAULT_POWER_LIMIT_MSG_ON,
    DEFAULT_POWER_LIMIT_NOTIFY_TELEGRAM,
    DEFAULT_POWER_LIMIT_NOTIFY_TTS,
    DEFAULT_POWER_LIMIT_RESTORE_MIN,
    EMERGENCY_PRE_NIGHT_MIN,
    EMERGENCY_PRE_NIGHT_MIN,
    POWER_LIMIT_MODE_MULTI,
    SWITCH_KEY_EMERGENCY,
    POWER_LIMIT_MODE_SINGLE,
    POWER_LIMIT_RESTORE_STAGGER_MIN,
    POWER_LIMIT_SPIKE_SEC,
    CONFIG_MODE_SIMPLE_FV,
    DEFAULT_SIMPLE_DRY_ENABLED,
    DEFAULT_SIMPLE_DRY_MAX_MIN,
    DEFAULT_SIMPLE_NO_AUTO_ON_NIGHT,
    DEFAULT_SIMPLE_TURN_ON_OFFSET_EXT,
    DEFAULT_SIMPLE_TURN_ON_OFFSET_INT,
    DEFAULT_SIMPLE_TURN_ON_OFFSET_EXT,
    DEFAULT_SIMPLE_TURN_ON_OFFSET_INT,
    DEFAULT_SIMPLE_MSG_AC_OFF,
    DEFAULT_SIMPLE_MSG_AC_OFF_FV,
    DEFAULT_SIMPLE_MSG_AC_ON,
    DEFAULT_SIMPLE_MSG_AC_ON_FV,
    DEFAULT_SIMPLE_MSG_AC_ON_NIGHT,
    DEFAULT_SIMPLE_MSG_AC_ON_EMERGENCY,
    DEFAULT_SIMPLE_MSG_DOOR_CLOSE,
    DEFAULT_SIMPLE_MSG_DOOR_OPEN,
    DEFAULT_SIMPLE_MSG_NIGHT_END,
    DEFAULT_SIMPLE_MSG_NIGHT_START,
    DEFAULT_SIMPLE_MSG_WINDOW_CLOSE,
    DEFAULT_SIMPLE_MSG_WINDOW_OPEN,
    DEFAULT_SIMPLE_NIGHT_END,
    DEFAULT_SIMPLE_NIGHT_START,
    DEFAULT_SIMPLE_SUNSET_ANTICIPATE_H,
    DEFAULT_SIMPLE_MSG_TEMP_CHANGE,
    DEFAULT_SIMPLE_NOTIFY_TEL_AC_OFF,
    DEFAULT_SIMPLE_NOTIFY_TEL_AC_ON,
    DEFAULT_SIMPLE_NOTIFY_TEL_DOOR_CLOSE,
    DEFAULT_SIMPLE_NOTIFY_TEL_DOOR_OPEN,
    DEFAULT_SIMPLE_NOTIFY_TEL_NIGHT_END,
    DEFAULT_SIMPLE_NOTIFY_TEL_NIGHT_START,
    DEFAULT_SIMPLE_NOTIFY_TEL_TEMP_CHANGE,
    DEFAULT_SIMPLE_NOTIFY_TEL_WINDOW_CLOSE,
    DEFAULT_SIMPLE_NOTIFY_TEL_WINDOW_OPEN,
    DEFAULT_SIMPLE_NOTIFY_TTS_AC_OFF,
    DEFAULT_SIMPLE_NOTIFY_TTS_AC_ON,
    DEFAULT_SIMPLE_NOTIFY_TTS_DOOR_CLOSE,
    DEFAULT_SIMPLE_NOTIFY_TTS_DOOR_OPEN,
    DEFAULT_SIMPLE_NOTIFY_TTS_NIGHT_END,
    DEFAULT_SIMPLE_NOTIFY_TTS_NIGHT_START,
    DEFAULT_SIMPLE_NOTIFY_TTS_TEMP_CHANGE,
    DEFAULT_SIMPLE_NOTIFY_TTS_WINDOW_CLOSE,
    DEFAULT_SIMPLE_NOTIFY_TTS_WINDOW_OPEN,
    DEFAULT_SIMPLE_QUIET_NIGHT_NOTIFY,
    DEFAULT_SIMPLE_QUIET_NIGHT_TTS,
    DEFAULT_SIMPLE_TARGET_DAY,
    DEFAULT_SIMPLE_TARGET_NIGHT,
    SIMPLE_EXT_DRY_HIGH,
    SIMPLE_EXT_DRY_LOW,
    SIMPLE_EXT_HOT_OFFSET,
    SIMPLE_NIGHT_END_LIMBO_H,
    SIMPLE_EXT_MILD_OFFSET,
    SIMPLE_EXT_SETPOINT_HOT,
    SIMPLE_EXT_SETPOINT_MILD,
    SIMPLE_EXT_SHUTOFF_MIN,
    SIMPLE_EXT_SHUTOFF_OFFSET,
    SIMPLE_EXT_SLOW_OFFSET,
    SIMPLE_EXT_WARM_OFFSET,
    SIMPLE_INT_DRY_HIGH,
    SIMPLE_INT_DRY_LOW,
    SIMPLE_INT_AT_TARGET,
    SIMPLE_INT_HOT_OFFSET,
    SIMPLE_INT_SETPOINT_HOT,
    SIMPLE_INT_SETPOINT_MILD,
    SIMPLE_INT_SHUTOFF_MIN,
    SIMPLE_INT_SHUTOFF_OFFSET,
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
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.COOL, HVACMode.DRY]
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

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=get_conf(entry, CONF_NAME, DEFAULT_NAME),
            manufacturer="Termostato Intelligente FV",
            model="Termostato Intelligente",
        )
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

        # --- Protezione potenza ---
        self._power_limit_high_since: datetime | None = None  # da quando il consumo è sopra soglia
        self._power_limit_off: bool = False                    # True se spento per power limit
        self._power_limit_off_at: datetime | None = None       # quando è stato spento
        self._power_limit_low_since: datetime | None = None    # da quando il consumo è sotto soglia-isteresi

        # --- Emergenza caldo ---
        self._emergency_notified: bool = False  # evita notifiche doppie

        # --- Modo semplificato ---
        self._simple_shutoff_since: datetime | None = None  # timer spegnimento per target raggiunto
        self._simple_was_night: bool = False                 # per rilevare transizione notte→giorno
        self._simple_night_auto_on: bool = False             # acceso automaticamente di notte
        self._simple_dry_since: datetime | None = None       # da quando è in modalità dry (diagnostica)
        self._simple_dry_end: datetime | None = None         # timestamp UTC di fine DRY (assoluto)
        self._dry_cancel_timer: callable | None = None       # cancel function async_track_point_in_time
        self._door_debounce_cancel = None                          # timer debounce porta
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
        if state.state == "dry":
            return HVACMode.DRY
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
            # --- diagnostica DRY ---
            "dry_since": self._simple_dry_since.isoformat() if self._simple_dry_since else None,
            "dry_end": self._simple_dry_end.isoformat() if self._simple_dry_end else None,
            "dry_elapsed_min": round((dt_util.utcnow() - self._simple_dry_since).total_seconds() / 60, 1) if self._simple_dry_since else None,
        }

    # ------------------------------------------------------------------
    # Ciclo di vita
    # ------------------------------------------------------------------

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        # Recupera dry_end dall'ultimo stato salvato (RestoreEntity).
        # Se il clima era in DRY prima del riavvio, rischeduliamo il timer
        # a partire dal timestamp assoluto salvato.
        last_state = await self.async_get_last_state()
        if last_state and last_state.attributes.get("dry_end"):
            try:
                dry_end = dt_util.parse_datetime(last_state.attributes["dry_end"])
                if dry_end is not None:
                    real_state = self.hass.states.get(self._climate_entity)
                    if real_state and real_state.state == "dry":
                        dry_since_str = last_state.attributes.get("dry_since")
                        if dry_since_str:
                            try:
                                self._simple_dry_since = dt_util.parse_datetime(dry_since_str)
                            except Exception:
                                self._simple_dry_since = dt_util.utcnow()
                        self._simple_dry_end = dry_end
                        # async_track_point_in_time scatta alla data indicata; se è già
                        # nel passato scatta al prossimo tick dell'event loop — perfetto
                        # per gestire il caso "HA spento durante il countdown DRY".
                        self._dry_cancel_timer = async_track_point_in_time(
                            self.hass, self._async_dry_to_cool, dry_end
                        )
                        _LOGGER.info(
                            "%s: riavvio con DRY — timer ripristinato, scade alle %s",
                            self._attr_name, dry_end.isoformat(),
                        )
            except Exception as exc:
                _LOGGER.warning("%s: errore recupero dry_end dopo riavvio: %s", self._attr_name, exc)

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
            if new_state and new_state.state == "off":
                # Spegnimento reale (intenzionale) — cancel timer DRY e reset completo
                self._cancel_dry_timer("off_state_change")
                self._fv_surplus_buffer = []
                self._night_below_since = None
                self._night_auto_on = False
                self._fv_auto_on = False
                self._simple_night_auto_on = False
                self._simple_shutoff_since = None
                self._power_limit_high_since = None
                self._power_limit_low_since = None
            elif new_state and new_state.state in ("unknown", "unavailable"):
                # Blip transitorio — NON toccare il timer DRY, prosegue normalmente
                _LOGGER.debug(
                    "%s: climatizzatore temporaneamente %s — timer DRY preservato",
                    self._attr_name, new_state.state,
                )
            elif new_state and new_state.state == "dry":
                if self._simple_dry_end is None:
                    # Tornato in DRY senza timer attivo (es. set manuale da UI/altra
                    # automazione/telecomando) — riarma subito, alla transizione
                    _LOGGER.warning("%s: [DRY-TRACE] rilevato DRY via state_change senza timer attivo — riavvio", self._attr_name)
                    self._schedule_dry_timer("dry_rilevato_su_state_change")
                else:
                    _LOGGER.warning(
                        "%s: [DRY-TRACE] state_change a DRY ma timer già attivo (dry_end=%s) — nessuna azione",
                        self._attr_name, self._simple_dry_end.isoformat(),
                    )
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        if self._window_cancel_timer is not None:
            self._window_cancel_timer()
            self._window_cancel_timer = None
        if self._dry_cancel_timer is not None:
            self._dry_cancel_timer()
            self._dry_cancel_timer = None
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
        if hvac_mode == HVACMode.OFF:
            await self.hass.services.async_call("climate", "turn_off", {"entity_id": self._climate_entity}, blocking=True)
        elif hvac_mode == HVACMode.DRY:
            await self.hass.services.async_call("climate", "set_hvac_mode", {"entity_id": self._climate_entity, "hvac_mode": "dry"}, blocking=True)
            self._schedule_dry_timer("set_hvac_mode_manuale_da_ui")
        else:
            await self.hass.services.async_call("climate", "turn_on", {"entity_id": self._climate_entity}, blocking=True)
        self.async_write_ha_state()

    # ------------------------------------------------------------------
    # Loop periodico
    # ------------------------------------------------------------------

    async def _async_periodic_update(self, now: datetime | None = None) -> None:
        if not self._switch_state(SWITCH_KEY_MASTER, True):
            return
        if self._is_window_open():
            return

        mode = self._get_config_mode()

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

        # Protezione potenza — ha precedenza su tutto
        await self._async_handle_power_limit()

        # Se spento per power limit non fare altro
        if self._power_limit_off:
            return
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
        # --- Fallback DRY→COOL ---
        # Il meccanismo primario è async_track_point_in_time schedulato da _schedule_dry_timer.
        # Questo fallback copre il caso raro in cui il Gree era unavailable al momento
        # esatto dello scatto del timer (il callback ha trovato stato != "dry" e non ha
        # transitato). Ogni 5 minuti verifichiamo: se dry_end è nel passato e il clima
        # è ancora in DRY, transitiamo a COOL adesso.
        if self._simple_dry_end is not None:
            real_state_dry = self.hass.states.get(self._climate_entity)
            if real_state_dry and real_state_dry.state == "dry":
                if dt_util.utcnow() >= self._simple_dry_end:
                    _LOGGER.warning(
                        "%s: [DRY-TRACE] fallback polling — timer già scaduto, transizione ora (set_hvac_mode cool)",
                        self._attr_name,
                    )
                    await self.hass.services.async_call(
                        "climate", "set_hvac_mode", {"entity_id": self._climate_entity, "hvac_mode": "cool"}, blocking=True
                    )
                    self._cancel_dry_timer("fallback_polling_dry_end_scaduto")

        use_internal = not bool(self._temp_sensor)
        temp = self._simple_read_temp()
        if temp is None:
            return

        # Protezione potenza — ha precedenza su tutto
        await self._async_handle_power_limit()
        if self._power_limit_off:
            return

        night_now = self._simple_is_night()
        night_just_ended = self._simple_was_night and not night_now
        night_just_started = not self._simple_was_night and night_now
        self._simple_was_night = night_now

        target = self._simple_current_target()

        # Notifica inizio modalità notturna
        if night_just_started:
            await self._async_simple_notify_night_start(target)

        # Spegnimento fine notte — deve avvenire PRIMA del check limbo, perché
        # il limbo scatta subito dopo night_end e bloccherebbe questo blocco
        # per l'intera ora successiva (bug: lo spegnimento non avveniva mai).
        if night_just_ended:
            self._simple_night_auto_on = False  # reset — non è più notte
            await self._async_handle_night_end_shutoff()
            await self._async_simple_notify_night_end()

        # Ora di limbo dopo fine notte — non fare altro (accensioni/regolazioni)
        if self._simple_is_in_limbo():
            _LOGGER.debug("%s: [semplificato] ora di limbo post-notte — nessuna azione", self._attr_name)
            return

        # Regolazione termica
        await self._async_handle_thermal_simple(temp, target, use_internal)

        # Accensione e spegnimento automatico (solo modo semplificato con FV)
        mode = self._get_config_mode()
        if mode == CONFIG_MODE_SIMPLE_FV:
            dry_enabled = bool(get_conf(self.entry, CONF_SIMPLE_DRY_ENABLED, DEFAULT_SIMPLE_DRY_ENABLED))
            # Gestione emergenza caldo — ha precedenza sul FV normale
            await self._async_handle_emergency_heat(temp, target, use_internal, dry_enabled)
            # Se emergenza attiva salta logica FV normale
            if self._switch_state(SWITCH_KEY_EMERGENCY, False):
                return
            if self._switch_state(SWITCH_KEY_FV, True) and self._simple_within_fv_window():
                await self._async_handle_fv_turn_on_simple(temp, target)
            if bool(get_conf(self.entry, CONF_FV_SHUTOFF_ENABLED, DEFAULT_FV_SHUTOFF_ENABLED)):
                await self._async_handle_fv_shutoff_simple(temp, target)

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

    def _get_config_mode(self) -> str:
        """Restituisce config_mode corretto, deducendolo dal fv_sensor se necessario.
        
        Tabella conversione valori vecchi → nuovi:
        - "semplificato_fv" → CONFIG_MODE_SIMPLE_FV
        - "semplificato"    → CONFIG_MODE_SIMPLE
        - None / altro      → deduce da fv_sensor
        """
        VALID = (CONFIG_MODE_SIMPLE, CONFIG_MODE_SIMPLE_FV, CONFIG_MODE_FULL)
        # Tabella conversione vecchi valori
        CONVERSION = {
            "semplificato_fv": CONFIG_MODE_SIMPLE_FV,
            "semplificato": CONFIG_MODE_SIMPLE,
            "simple": CONFIG_MODE_SIMPLE,
            "simple_fv": CONFIG_MODE_SIMPLE_FV,
            "full": CONFIG_MODE_FULL,
        }
        mode = get_conf(self.entry, CONF_CONFIG_MODE, None)
        if mode in CONVERSION:
            return CONVERSION[mode]
        # Valore sconosciuto — deduce dalla presenza del sensore FV
        return CONFIG_MODE_SIMPLE_FV if self._fv_sensor else CONFIG_MODE_SIMPLE

    def _simple_is_night(self) -> bool:
        return self._in_time_window(
            get_conf(self.entry, CONF_SIMPLE_NIGHT_START, DEFAULT_SIMPLE_NIGHT_START),
            get_conf(self.entry, CONF_SIMPLE_NIGHT_END, DEFAULT_SIMPLE_NIGHT_END),
        )

    def _simple_is_in_limbo(self) -> bool:
        """True nell'ora dopo la fine della modalità notturna.

        Durante questo periodo il termostato non fa nulla — non accende,
        non spegne, non regola. Evita accensioni indesiderate causate dal
        cambio brusco di target (da notte a giorno).
        L'ora di limbo è fissa (SIMPLE_NIGHT_END_LIMBO_H = 1h).
        """
        if self._simple_is_night():
            return False
        night_end_str = get_conf(self.entry, CONF_SIMPLE_NIGHT_END, DEFAULT_SIMPLE_NIGHT_END)
        try:
            night_end_t = dt_time.fromisoformat(str(night_end_str))
        except ValueError:
            return False
        now_local = dt_util.now()
        night_end_dt = now_local.replace(
            hour=night_end_t.hour, minute=night_end_t.minute, second=0, microsecond=0
        )
        limbo_end_dt = night_end_dt + timedelta(hours=SIMPLE_NIGHT_END_LIMBO_H)
        return night_end_dt <= now_local < limbo_end_dt

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

    def _simple_within_fv_window(self) -> bool:
        """Finestra di accensione FV nel modo semplificato.

        Inizia alla fine della modalità notturna (night_end)
        e termina al tramonto - anticipate_h ore.
        Non richiede configurazione oraria — usa sun.sun e la fascia notturna.
        """
        # Controlla che il sole sia sopra l'orizzonte
        sun_state = self.hass.states.get("sun.sun")
        if sun_state is None or sun_state.state != "above_horizon":
            return False

        now_local = dt_util.now()

        # Inizio finestra = fine modalità notturna
        night_end_str = get_conf(self.entry, CONF_SIMPLE_NIGHT_END, DEFAULT_SIMPLE_NIGHT_END)
        try:
            night_end_t = dt_time.fromisoformat(str(night_end_str))
        except ValueError:
            return False
        night_end_dt = now_local.replace(
            hour=night_end_t.hour, minute=night_end_t.minute, second=0, microsecond=0
        )

        # Fine finestra = tramonto - anticipate_h
        next_setting_str = sun_state.attributes.get("next_setting")
        if not next_setting_str:
            return False
        try:
            sunset_dt = dt_util.as_local(dt_util.parse_datetime(str(next_setting_str)))
        except (ValueError, TypeError):
            return False
        anticipate_h = float(get_conf(self.entry, CONF_SIMPLE_SUNSET_ANTICIPATE_H, DEFAULT_SIMPLE_SUNSET_ANTICIPATE_H))
        cutoff_dt = sunset_dt - timedelta(hours=anticipate_h)

        return night_end_dt <= now_local <= cutoff_dt

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

        Nel modo semplificato con FV: se il clima è spento non accende —
        ci pensa solo la logica FV. La logica termica regola solo se già acceso.
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
        no_auto_on_night = bool(get_conf(self.entry, CONF_SIMPLE_NO_AUTO_ON_NIGHT, DEFAULT_SIMPLE_NO_AUTO_ON_NIGHT))

        config_mode = self._get_config_mode()
        current_state = real_state.state if real_state else "off"
        is_on = self.hvac_mode == HVACMode.COOL or current_state == "dry"
        is_night = self._simple_is_night()
        if config_mode == CONFIG_MODE_SIMPLE_FV and not is_on and not is_night:
            return
        if no_auto_on_night and is_night and not is_on:
            return

        if use_internal:
            await self._async_thermal_simple_internal(temp, target, internal_temp, real_state, dry_enabled, is_night)
        else:
            await self._async_thermal_simple_external(temp, target, internal_temp, real_state, dry_enabled, is_night)

    async def _async_thermal_simple_internal(
        self, temp: float, target: float, internal_temp: float | None, real_state, dry_enabled: bool, is_night: bool = False
    ) -> None:
        """Logica termica con sonda interna (interi).

        Soglia accensione: target + turn_on_offset (default +1°C).
        All accensione: DRY 30 min (se abilitato), poi fascia COOL.
        Mai tornare in DRY quando già in COOL.

        Fasce COOL (target es. 25°C):
          temp ≥ target+3 (28°C) → ventola alta,  setpoint = internal-3
          temp ≥ target+2 (27°C) → ventola media, setpoint = internal-2
          temp ≥ target+1 (26°C) → ventola media, setpoint = internal-1
          temp = target   (25°C) → ventola bassa, setpoint = internal
          temp < target          → ventola bassa, setpoint = internal per 15 min → spegne
        """
        turn_on_offset = float(get_conf(self.entry, CONF_SIMPLE_TURN_ON_OFFSET, DEFAULT_SIMPLE_TURN_ON_OFFSET_INT))
        now = dt_util.utcnow()
        current_mode = real_state.state if real_state else "off"
        is_on = self.hvac_mode == HVACMode.COOL or current_mode == "dry"

        # --- Spegnimento per target raggiunto ---
        if is_on:
            if temp < target:
                if self._simple_shutoff_since is None:
                    self._simple_shutoff_since = now
                elif (now - self._simple_shutoff_since) >= timedelta(minutes=SIMPLE_INT_SHUTOFF_MIN):
                    _LOGGER.info("%s: [semplificato] spegnimento target (int, temp=%.0f < target=%.0f)", self._attr_name, temp, target)
                    await self.hass.services.async_call("climate", "turn_off", {"entity_id": self._climate_entity}, blocking=True)
                    self._simple_shutoff_since = None
                    self._cancel_dry_timer("spegnimento_target_int")
                    self._simple_night_auto_on = False
                    self._fv_auto_on = False
                    await self._async_simple_notify_ac_off(temp, target)
                    return
            else:
                self._simple_shutoff_since = None

        # --- In DRY: il timer async_track_point_in_time gestisce il passaggio a COOL ---
        if current_mode == "dry":
            if self._simple_dry_end is None:
                _LOGGER.warning("%s: [int] DRY senza timer schedulato — riavvio timer", self._attr_name)
                self._schedule_dry_timer("safety_dry_senza_timer_internal")
            return

        # --- Accensione (clima spento) ---
        if not is_on:
            if temp >= target + turn_on_offset:
                if dry_enabled:
                    _LOGGER.info("%s: [semplificato] accensione DRY (int, temp=%.0f)", self._attr_name, temp)
                    await self.hass.services.async_call("climate", "set_hvac_mode", {"entity_id": self._climate_entity, "hvac_mode": "dry"}, blocking=True)
                    self._schedule_dry_timer("accensione_dry_internal")
                else:
                    _LOGGER.info("%s: [semplificato] accensione COOL (int, temp=%.0f)", self._attr_name, temp)
                    await self.hass.services.async_call("climate", "turn_on", {"entity_id": self._climate_entity}, blocking=True)
                self._simple_night_auto_on = self._simple_is_night()
                self._fv_auto_on = False
                ac_type_int = "notturna" if self._simple_is_night() else "termica"
                await self._async_simple_notify_ac_on(temp, target, ac_type=ac_type_int)
            return

        # --- Regolazione COOL ---
        if internal_temp is None:
            return

        internal_int = int(internal_temp)

        if temp >= target + 3:
            new_setpoint = internal_int - 3
            fan = "high"
        elif temp >= target + 2:
            new_setpoint = internal_int - 2
            fan = "medium"
        elif temp >= target + 1:
            new_setpoint = internal_int - 1
            fan = "low" if is_night else "medium"
        else:
            # temp = target o leggermente sopra — ventola bassa, setpoint = interna
            new_setpoint = internal_int
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
        self, temp: float, target: float, internal_temp: float | None, real_state, dry_enabled: bool, is_night: bool = False
    ) -> None:
        """Logica termica con sonda esterna (decimali).

        Soglia accensione: target + turn_on_offset (default +0.8°C).
        All accensione: DRY 30 min (se abilitato), poi fascia COOL.
        Mai tornare in DRY quando già in COOL.

        Fasce COOL (target es. 25°C):
          temp ≥ target+3.1 (28.1°C) → ventola alta,  setpoint = internal-3
          temp ≥ target+1.7 (26.7°C) → ventola media, setpoint = internal-2
          temp ≥ target+0.7 (25.7°C) → ventola media, setpoint = internal-1
          temp ≥ target+0.1 (25.1°C) → ventola bassa, setpoint = internal-1
          temp = target    (25.0°C)  → ventola bassa, setpoint = internal
          temp < target              → ventola bassa, setpoint = internal per 15 min → spegne
        """
        turn_on_offset = float(get_conf(self.entry, CONF_SIMPLE_TURN_ON_OFFSET, DEFAULT_SIMPLE_TURN_ON_OFFSET_EXT))
        now = dt_util.utcnow()
        current_mode = real_state.state if real_state else "off"
        is_on = self.hvac_mode == HVACMode.COOL or current_mode == "dry"

        # --- Spegnimento per target raggiunto ---
        if is_on:
            if temp < target:
                if self._simple_shutoff_since is None:
                    self._simple_shutoff_since = now
                elif (now - self._simple_shutoff_since) >= timedelta(minutes=SIMPLE_EXT_SHUTOFF_MIN):
                    _LOGGER.info("%s: [semplificato] spegnimento target (ext, temp=%.1f < target=%.1f)", self._attr_name, temp, target)
                    await self.hass.services.async_call("climate", "turn_off", {"entity_id": self._climate_entity}, blocking=True)
                    self._simple_shutoff_since = None
                    self._cancel_dry_timer("spegnimento_target_ext")
                    self._simple_night_auto_on = False
                    self._fv_auto_on = False
                    await self._async_simple_notify_ac_off(temp, target)
                    return
            else:
                self._simple_shutoff_since = None

        # --- Passaggio da DRY a COOL dopo timer ---
        if current_mode == "dry":
            if self._simple_dry_end is None:
                _LOGGER.warning("%s: [ext] DRY senza timer schedulato — riavvio timer", self._attr_name)
                self._schedule_dry_timer("safety_dry_senza_timer_external")
            return

        # --- Accensione (clima spento) ---
        if not is_on:
            if temp >= target + turn_on_offset:
                if dry_enabled:
                    _LOGGER.info("%s: [semplificato] accensione DRY (ext, temp=%.1f)", self._attr_name, temp)
                    await self.hass.services.async_call("climate", "set_hvac_mode", {"entity_id": self._climate_entity, "hvac_mode": "dry"}, blocking=True)
                    self._schedule_dry_timer("accensione_dry_external")
                else:
                    _LOGGER.info("%s: [semplificato] accensione COOL (ext, temp=%.1f)", self._attr_name, temp)
                    await self.hass.services.async_call("climate", "turn_on", {"entity_id": self._climate_entity}, blocking=True)
                self._simple_night_auto_on = self._simple_is_night()
                self._fv_auto_on = False
                ac_type_ext = "notturna" if self._simple_is_night() else "termica"
                await self._async_simple_notify_ac_on(temp, target, ac_type=ac_type_ext)
            return

        # --- Regolazione COOL ---
        if internal_temp is None:
            return

        if temp >= target + 3.1:
            new_setpoint = internal_temp - 3.0
            fan = "high"
        elif temp >= target + 1.7:
            new_setpoint = internal_temp - 2.0
            fan = "medium"
        elif temp >= target + 0.7:
            new_setpoint = internal_temp - 1.0
            fan = "low" if is_night else "medium"
        elif temp >= target + 0.1:
            new_setpoint = internal_temp - 1.0
            fan = "low"
        else:
            # temp = target — ventola bassa, setpoint = interna
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
        """Accensione FV per il modo semplificato.

        Accende solo se:
        1. Clima completamente spento (non in DRY, non in COOL)
        2. Temperatura ≥ soglia configurata
        3. FV surplus > margine E SOC > minimo
        4. Priorità e stagger rispettati
        5. Non siamo in limbo post-notte
        """
        # Non intervenire se il clima è già acceso in qualsiasi modalità (COOL o DRY)
        real_state = self.hass.states.get(self._climate_entity)
        if real_state and real_state.state not in ("off", "unknown", "unavailable"):
            return
        if self._simple_is_in_limbo():
            return

        # Check temperatura
        use_internal = not bool(self._temp_sensor)
        turn_on_offset = float(get_conf(self.entry, CONF_SIMPLE_TURN_ON_OFFSET,
            DEFAULT_SIMPLE_TURN_ON_OFFSET_INT if use_internal else DEFAULT_SIMPLE_TURN_ON_OFFSET_EXT))
        if temp < target + turn_on_offset:
            return  # non fa abbastanza caldo

        # Check FV
        if not (self._fv_sensor and self._consumption_sensor and self._battery_sensor):
            return
        fv = self._read_float(self._fv_sensor)
        consumo = self._read_float(self._consumption_sensor)
        if fv is None or consumo is None:
            return

        # Check temperatura — deve fare abbastanza caldo per giustificare l'accensione
        use_internal = not bool(self._temp_sensor)
        turn_on_offset = float(get_conf(self.entry, CONF_SIMPLE_TURN_ON_OFFSET,
            DEFAULT_SIMPLE_TURN_ON_OFFSET_INT if use_internal else DEFAULT_SIMPLE_TURN_ON_OFFSET_EXT))
        if temp < target + turn_on_offset:
            return  # non fa abbastanza caldo

        margin = float(get_conf(self.entry, CONF_FV_MARGIN_W, DEFAULT_FV_MARGIN_W))
        soc_min = float(get_conf(self.entry, CONF_SOC_MIN, DEFAULT_SOC_MIN))

        # Check SOC solo se la batteria è configurata
        if self._battery_sensor:
            soc = self._read_float(self._battery_sensor)
            if soc is None:
                return  # Sensore batteria non disponibile — aspetta
            if soc < soc_min:
                return  # Batteria sotto soglia — riprova al prossimo ciclo

        if not (fv > consumo + margin):
            return  # FV insufficiente — riprova al prossimo ciclo

        # Check stagger e priorità
        coord = self.hass.data.setdefault(DOMAIN, {}).setdefault("_coordination", {})
        stagger_min = float(get_conf(self.entry, CONF_FV_STAGGER_MIN, DEFAULT_FV_STAGGER_MIN))
        last_on = coord.get("last_fv_turn_on")
        if last_on is not None and (dt_util.utcnow() - last_on) < timedelta(minutes=stagger_min):
            return

        # Accensione — sempre DRY prima (se abilitato)
        dry_enabled = bool(get_conf(self.entry, CONF_SIMPLE_DRY_ENABLED, DEFAULT_SIMPLE_DRY_ENABLED))
        now = dt_util.utcnow()
        if dry_enabled:
            _LOGGER.info("%s: [semplificato FV] accensione DRY (fv=%.0fW, consumo=%.0fW)", self._attr_name, fv, consumo)
            await self.hass.services.async_call("climate", "set_hvac_mode", {"entity_id": self._climate_entity, "hvac_mode": "dry"}, blocking=True)
            self._schedule_dry_timer("accensione_fv_turn_on_simple")
        else:
            _LOGGER.info("%s: [semplificato FV] accensione COOL (fv=%.0fW, consumo=%.0fW)", self._attr_name, fv, consumo)
            await self.hass.services.async_call("climate", "turn_on", {"entity_id": self._climate_entity}, blocking=True)
            self._cancel_dry_timer("accensione_fv_cool_no_dry")

        coord["last_fv_turn_on"] = now
        self._fv_auto_on = True
        self._simple_night_auto_on = False
        soc_val = self._read_float(self._battery_sensor) or 0
        await self._async_simple_notify_ac_on(temp, target, ac_type="fv", fv=fv, consumo=consumo, soc=soc_val)

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
        """Spegnimento e riaccensione FV per il modo semplificato.

        4 casi per spegnimento:
        1. Acceso di notte automaticamente → non spegnere mai per FV
        2. Acceso dal FV → spegne sempre se FV insufficiente, riaccende quando torna
        3. Acceso manualmente prima di tramonto-Xh → spegne se FV insufficiente
        4. Acceso manualmente dopo tramonto-Xh → non toccare

        Riaccensione: se il clima è spento per FV e la produzione torna
        sufficiente + temperatura ancora sopra soglia → riaccende da DRY.
        """
        if not (self._fv_sensor and self._consumption_sensor):
            return

        fv = self._read_float(self._fv_sensor)
        consumo = self._read_float(self._consumption_sensor)
        if fv is None or consumo is None:
            return

        current_state = self.hass.states.get(self._climate_entity)
        is_on = self.hvac_mode == HVACMode.COOL or (
            current_state and current_state.state == "dry"
        )

        # --- Riaccensione dopo spegnimento FV ---
        # Se il clima è spento, era stato acceso dal FV, e il FV è tornato sufficiente
        if not is_on and self._fv_auto_on:
            margin = float(get_conf(self.entry, CONF_FV_MARGIN_W, DEFAULT_FV_MARGIN_W))
            soc_min = float(get_conf(self.entry, CONF_SOC_MIN, DEFAULT_SOC_MIN))
            soc = self._read_float(self._battery_sensor)
            use_internal = not bool(self._temp_sensor)
            turn_on_offset = float(get_conf(self.entry, CONF_SIMPLE_TURN_ON_OFFSET,
                DEFAULT_SIMPLE_TURN_ON_OFFSET_INT if use_internal else DEFAULT_SIMPLE_TURN_ON_OFFSET_EXT))
            fv_ok = fv > consumo + margin and (soc is None or soc > soc_min)
            temp_ok = temp >= target + turn_on_offset
            if fv_ok and temp_ok and not self._simple_is_in_limbo():
                dry_enabled = bool(get_conf(self.entry, CONF_SIMPLE_DRY_ENABLED, DEFAULT_SIMPLE_DRY_ENABLED))
                now = dt_util.utcnow()
                if dry_enabled:
                    _LOGGER.info("%s: [semplificato FV] riaccensione DRY dopo calo FV", self._attr_name)
                    await self.hass.services.async_call("climate", "set_hvac_mode", {"entity_id": self._climate_entity, "hvac_mode": "dry"}, blocking=True)
                    self._schedule_dry_timer("riaccensione_fv_dopo_calo")
                else:
                    _LOGGER.info("%s: [semplificato FV] riaccensione COOL dopo calo FV", self._attr_name)
                    await self.hass.services.async_call("climate", "turn_on", {"entity_id": self._climate_entity}, blocking=True)
                    self._cancel_dry_timer("riaccensione_fv_cool_no_dry")
                self._fv_surplus_buffer = []
                soc_val2 = self._read_float(self._battery_sensor) or 0
                fv2 = self._read_float(self._fv_sensor) or 0
                consumo2 = self._read_float(self._consumption_sensor) or 0
                await self._async_simple_notify_ac_on(temp, target, ac_type="fv", fv=fv2, consumo=consumo2, soc=soc_val2)
            return

        if not is_on:
            self._fv_surplus_buffer = []
            return

        # Caso 1: acceso dalla modalità notturna → FV non interviene
        if self._simple_night_auto_on:
            self._fv_surplus_buffer = []
            return

        # Caso 2/3/4: verifica se può spegnere
        shutoff_manual = bool(get_conf(self.entry, CONF_FV_SHUTOFF_MANUAL, DEFAULT_FV_SHUTOFF_MANUAL))
        if not self._fv_auto_on and not self._simple_can_control_manual() and not shutoff_manual:
            self._fv_surplus_buffer = []
            return

        # Sliding window
        surplus = fv - consumo
        threshold = float(get_conf(self.entry, CONF_FV_SHUTOFF_THRESHOLD, DEFAULT_FV_SHUTOFF_THRESHOLD))
        delay_min = int(get_conf(self.entry, CONF_FV_SHUTOFF_DELAY_MIN, DEFAULT_FV_SHUTOFF_DELAY_MIN))

        self._fv_surplus_buffer.append(surplus)
        if len(self._fv_surplus_buffer) > delay_min:
            self._fv_surplus_buffer.pop(0)

        _LOGGER.debug(
            "%s: [semplificato FV] shutoff buffer %s (soglia=%.0f)",
            self._attr_name, [round(s) for s in self._fv_surplus_buffer], threshold,
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

        _LOGGER.info("%s: [semplificato FV] spegnimento per FV (fv=%.0fW, consumo=%.0fW)", self._attr_name, fv, consumo)
        await self.hass.services.async_call("climate", "turn_off", {"entity_id": self._climate_entity}, blocking=True)
        coord["last_fv_shutoff"] = now
        self._fv_surplus_buffer = []
        # NON resettiamo _fv_auto_on così la riaccensione sa che era il FV ad averlo acceso
        await self._async_simple_notify_ac_off(temp, target, fv_shutoff=True)


    async def _async_simple_notify_ac_on(
        self, temp: float, target: float = 0,
        ac_type: str = "termica",
        fv: float = 0, consumo: float = 0, soc: float = 0
    ) -> None:
        """Notifica accensione con parametri distinti per tipo.

        ac_type: 'termica', 'fv', 'notturna', 'emergenza'
        """
        surplus = round(fv - consumo) if fv and consumo else 0
        if ac_type == "fv":
            tpl = DEFAULT_SIMPLE_MSG_AC_ON_FV
            vars = {"name": self._attr_name, "temp": round(temp, 1), "target": round(target, 1),
                    "fv": round(fv), "surplus": surplus, "soc": round(soc, 1)}
        elif ac_type == "notturna":
            tpl = DEFAULT_SIMPLE_MSG_AC_ON_NIGHT
            vars = {"name": self._attr_name, "temp": round(temp, 1), "target": round(target, 1)}
        elif ac_type == "emergenza":
            tpl = DEFAULT_SIMPLE_MSG_AC_ON_EMERGENCY
            vars = {"name": self._attr_name, "temp": round(temp, 1), "target": round(target, 1)}
        else:
            tpl = DEFAULT_SIMPLE_MSG_AC_ON
            vars = {"name": self._attr_name, "temp": round(temp, 1), "target": round(target, 1)}
        msg = await self._async_render(tpl, vars)
        if bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_TTS_AC_ON, DEFAULT_SIMPLE_NOTIFY_TTS_AC_ON)):
            await self._async_simple_speak(msg)
        if bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_TEL_AC_ON, DEFAULT_SIMPLE_NOTIFY_TEL_AC_ON)):
            await self._async_simple_notify(msg)

    async def _async_simple_notify_ac_off(self, temp: float, target: float, fv_shutoff: bool = False) -> None:
        tpl = DEFAULT_SIMPLE_MSG_AC_OFF_FV if fv_shutoff else DEFAULT_SIMPLE_MSG_AC_OFF
        msg = await self._async_render(tpl, {"name": self._attr_name, "temp": round(temp, 1), "target": round(target, 1)})
        if bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_TTS_AC_OFF, DEFAULT_SIMPLE_NOTIFY_TTS_AC_OFF)):
            await self._async_simple_speak(msg)
        if bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_TEL_AC_OFF, DEFAULT_SIMPLE_NOTIFY_TEL_AC_OFF)):
            await self._async_simple_notify(msg)

    async def _async_simple_notify_temp_change(self, temp: float, target: float) -> None:
        msg = await self._async_render(DEFAULT_SIMPLE_MSG_TEMP_CHANGE, {"name": self._attr_name, "temp": round(temp, 1), "target": round(target, 1)})
        if bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_TTS_TEMP_CHANGE, DEFAULT_SIMPLE_NOTIFY_TTS_TEMP_CHANGE)):
            await self._async_simple_speak(msg)
        if bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_TEL_TEMP_CHANGE, DEFAULT_SIMPLE_NOTIFY_TEL_TEMP_CHANGE)):
            await self._async_simple_notify(msg)

    async def _async_simple_notify_night_start(self, target: float) -> None:
        msg = await self._async_render(DEFAULT_SIMPLE_MSG_NIGHT_START, {"name": self._attr_name, "target": round(target, 1)})
        if bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_TTS_NIGHT_START, DEFAULT_SIMPLE_NOTIFY_TTS_NIGHT_START)):
            await self._async_simple_speak(msg)
        if bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_TEL_NIGHT_START, DEFAULT_SIMPLE_NOTIFY_TEL_NIGHT_START)):
            await self._async_simple_notify(msg, bypass_quiet=True)

    async def _async_simple_notify_night_end(self) -> None:
        msg = await self._async_render(DEFAULT_SIMPLE_MSG_NIGHT_END, {"name": self._attr_name})
        if bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_TTS_NIGHT_END, DEFAULT_SIMPLE_NOTIFY_TTS_NIGHT_END)):
            await self._async_simple_speak(msg)
        if bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_TEL_NIGHT_END, DEFAULT_SIMPLE_NOTIFY_TEL_NIGHT_END)):
            await self._async_simple_notify(msg, bypass_quiet=True)

    async def _async_simple_notify_door(self, is_open: bool) -> None:
        tpl = DEFAULT_SIMPLE_MSG_DOOR_OPEN if is_open else DEFAULT_SIMPLE_MSG_DOOR_CLOSE
        msg = await self._async_render(tpl, {"name": self._attr_name})
        if is_open:
            if bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_TTS_DOOR_OPEN, DEFAULT_SIMPLE_NOTIFY_TTS_DOOR_OPEN)):
                await self._async_simple_speak(msg)
            if bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_TEL_DOOR_OPEN, DEFAULT_SIMPLE_NOTIFY_TEL_DOOR_OPEN)):
                await self._async_simple_notify(msg)
        else:
            if bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_TTS_DOOR_CLOSE, DEFAULT_SIMPLE_NOTIFY_TTS_DOOR_CLOSE)):
                await self._async_simple_speak(msg)
            if bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_TEL_DOOR_CLOSE, DEFAULT_SIMPLE_NOTIFY_TEL_DOOR_CLOSE)):
                await self._async_simple_notify(msg)

    async def _async_simple_notify_window(self, is_open: bool, delay_min: int = 0, ac_was_on: bool = True) -> None:
        """Notifica apertura/chiusura finestra.

        Il messaggio cambia se il climatizzatore era acceso o spento nel
        momento dell'evento: se era già spento non ha senso dire
        "spengo tra X minuti" perché non c'è nulla da spegnere.
        """
        if is_open:
            if ac_was_on:
                tpl = DEFAULT_SIMPLE_MSG_WINDOW_OPEN
            else:
                tpl = "{{ name }}: finestra aperta (climatizzatore già spento)"
        else:
            if ac_was_on:
                tpl = DEFAULT_SIMPLE_MSG_WINDOW_CLOSE
            else:
                tpl = "{{ name }}: finestra chiusa (climatizzatore era spento)"
        msg = await self._async_render(tpl, {"name": self._attr_name, "delay": delay_min})
        if is_open:
            if bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_TTS_WINDOW_OPEN, DEFAULT_SIMPLE_NOTIFY_TTS_WINDOW_OPEN)):
                await self._async_simple_speak(msg)
            if bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_TEL_WINDOW_OPEN, DEFAULT_SIMPLE_NOTIFY_TEL_WINDOW_OPEN)):
                await self._async_simple_notify(msg)
        else:
            if bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_TTS_WINDOW_CLOSE, DEFAULT_SIMPLE_NOTIFY_TTS_WINDOW_CLOSE)):
                await self._async_simple_speak(msg)
            if bool(get_conf(self.entry, CONF_SIMPLE_NOTIFY_TEL_WINDOW_CLOSE, DEFAULT_SIMPLE_NOTIFY_TEL_WINDOW_CLOSE)):
                await self._async_simple_notify(msg)

    # ------------------------------------------------------------------
    # Emergenza caldo
    # ------------------------------------------------------------------

    async def _async_handle_emergency_heat(
        self, temp: float, target: float, use_internal: bool, dry_enabled: bool
    ) -> None:
        """Gestisce l'emergenza caldo nel modo semplificato FV e completo.

        Quando lo switch emergenza è attivo:
        - Accende se temp ≥ target + soglia_emergenza (ignorando FV)
        - Spegne per logica termica normale
        - Si disattiva automaticamente 5 min prima della notte
        - Si disattiva se temp scende sotto target + soglia_fine_emergenza
        """
        config_mode = get_conf(self.entry, CONF_CONFIG_MODE, CONFIG_MODE_FULL)
        if config_mode not in (CONFIG_MODE_SIMPLE_FV, CONFIG_MODE_FULL):
            return

        emergency_on = self._switch_state(SWITCH_KEY_EMERGENCY, False)

        # --- Disattivazione automatica pre-notte ---
        if emergency_on:
            night_start_str = get_conf(self.entry, CONF_SIMPLE_NIGHT_START, DEFAULT_SIMPLE_NIGHT_START)
            try:
                night_start_t = dt_time.fromisoformat(str(night_start_str))
            except ValueError:
                night_start_t = None

            if night_start_t:
                now_local = dt_util.now()
                night_start_dt = now_local.replace(
                    hour=night_start_t.hour, minute=night_start_t.minute, second=0, microsecond=0
                )
                pre_night_dt = night_start_dt - timedelta(minutes=EMERGENCY_PRE_NIGHT_MIN)
                if now_local >= pre_night_dt and not self._simple_is_night():
                    _LOGGER.info("%s: [emergenza] disattivazione pre-notte", self._attr_name)
                    # Spegni clima e disattiva switch
                    await self.hass.services.async_call("climate", "turn_off", {"entity_id": self._climate_entity}, blocking=True)
                    await self._async_emergency_set_switch(False)
                    await self._async_emergency_notify(False, temp, target)
                    self._emergency_notified = False
                    return

        # --- Disattivazione per temperatura rientrata ---
        if emergency_on:
            end_threshold = float(get_conf(self.entry, CONF_EMERGENCY_HEAT_END_THRESHOLD, DEFAULT_EMERGENCY_HEAT_END_THRESHOLD))
            if temp <= target + end_threshold:
                _LOGGER.info("%s: [emergenza] temperatura rientrata (temp=%.1f ≤ target+%.1f)", self._attr_name, temp, end_threshold)
                await self._async_emergency_set_switch(False)
                await self._async_emergency_notify(False, temp, target)
                self._emergency_notified = False
                return

        # --- Logica emergenza attiva ---
        if not emergency_on:
            return

        threshold = float(get_conf(self.entry, CONF_EMERGENCY_HEAT_THRESHOLD, DEFAULT_EMERGENCY_HEAT_THRESHOLD))
        real_state = self.hass.states.get(self._climate_entity)
        current_mode = real_state.state if real_state else "off"
        is_on = self.hvac_mode == HVACMode.COOL or current_mode == "dry"

        # Notifica accensione emergenza (una sola volta)
        if not self._emergency_notified:
            await self._async_emergency_notify(True, temp, target)
            self._emergency_notified = True

        # Accende se non è già acceso e supera la soglia
        if not is_on and temp >= target + threshold:
            internal_temp = self._read_float(self._climate_entity, attr="current_temperature")
            if dry_enabled:
                _LOGGER.info("%s: [emergenza] accensione DRY (temp=%.1f)", self._attr_name, temp)
                await self.hass.services.async_call("climate", "set_hvac_mode", {"entity_id": self._climate_entity, "hvac_mode": "dry"}, blocking=True)
                self._schedule_dry_timer("accensione_emergenza_dry")
            else:
                _LOGGER.info("%s: [emergenza] accensione COOL (temp=%.1f)", self._attr_name, temp)
                await self.hass.services.async_call("climate", "turn_on", {"entity_id": self._climate_entity}, blocking=True)
                self._cancel_dry_timer("accensione_emergenza_cool_no_dry")
            await self._async_simple_notify_ac_on(temp, target, ac_type="emergenza")

        # Regolazione termica normale (come semplificato puro)
        if is_on:
            internal_temp = self._read_float(self._climate_entity, attr="current_temperature")
            if use_internal:
                await self._async_thermal_simple_internal(temp, target, internal_temp, real_state, dry_enabled)
            else:
                await self._async_thermal_simple_external(temp, target, internal_temp, real_state, dry_enabled)

    async def _async_emergency_set_switch(self, state: bool) -> None:
        """Attiva/disattiva lo switch emergenza caldo."""
        entry_data = self.hass.data.get(DOMAIN, {}).get(self.entry.entry_id, {})
        switch = entry_data.get(SWITCH_KEY_EMERGENCY)
        if switch is not None:
            if state:
                await switch.async_turn_on()
            else:
                await switch.async_turn_off()

    async def _async_emergency_notify(self, is_on: bool, temp: float, target: float) -> None:
        """Notifica attivazione/disattivazione emergenza caldo."""
        notify_tts = bool(get_conf(self.entry, CONF_EMERGENCY_NOTIFY_TTS, DEFAULT_EMERGENCY_NOTIFY_TTS))
        notify_tel = bool(get_conf(self.entry, CONF_EMERGENCY_NOTIFY_TELEGRAM, DEFAULT_EMERGENCY_NOTIFY_TELEGRAM))
        if not notify_tts and not notify_tel:
            return

        config_mode = get_conf(self.entry, CONF_CONFIG_MODE, CONFIG_MODE_FULL)
        if is_on:
            tpl = get_conf(self.entry, CONF_EMERGENCY_MSG_ON, DEFAULT_EMERGENCY_MSG_ON) if config_mode == CONFIG_MODE_FULL else DEFAULT_EMERGENCY_MSG_ON
        else:
            tpl = get_conf(self.entry, CONF_EMERGENCY_MSG_OFF, DEFAULT_EMERGENCY_MSG_OFF) if config_mode == CONFIG_MODE_FULL else DEFAULT_EMERGENCY_MSG_OFF

        msg = await self._async_render(tpl, {"name": self._attr_name, "temp": round(temp, 1), "target": round(target, 1)})

        if notify_tts:
            await self._async_simple_speak(msg)
        if notify_tel:
            await self._async_simple_notify(msg)

    # ------------------------------------------------------------------
    # Protezione potenza (evita distacco contatore)
    # ------------------------------------------------------------------

    async def _async_handle_power_limit(self) -> None:
        """Spegne il clima se il consumo supera la soglia per 30 secondi.

        Riaccende quando il consumo scende sotto soglia-isteresi per X minuti.
        Modalità unico: gestisce solo se stesso.
        Modalità multi: usa priorità FV con stagger 2 min tra riaccensioni.
        """
        if not bool(get_conf(self.entry, CONF_POWER_LIMIT_ENABLED, DEFAULT_POWER_LIMIT_ENABLED)):
            return

        sensor = get_conf(self.entry, CONF_POWER_LIMIT_SENSOR)
        if not sensor:
            return

        consumo = self._read_float(sensor)
        if consumo is None:
            return

        max_w = float(get_conf(self.entry, CONF_POWER_LIMIT_MAX_W, DEFAULT_POWER_LIMIT_MAX_W))
        hysteresis_w = float(get_conf(self.entry, CONF_POWER_LIMIT_HYSTERESIS_W, DEFAULT_POWER_LIMIT_HYSTERESIS_W))
        restore_min = int(get_conf(self.entry, CONF_POWER_LIMIT_RESTORE_MIN, DEFAULT_POWER_LIMIT_RESTORE_MIN))
        mode = get_conf(self.entry, CONF_POWER_LIMIT_MODE, DEFAULT_POWER_LIMIT_MODE)
        now = dt_util.utcnow()

        current_state = self.hass.states.get(self._climate_entity)
        is_on = current_state and current_state.state not in ("off", "unknown", "unavailable")

        # --- Spegnimento per eccesso consumo ---
        if is_on and not self._power_limit_off:
            if consumo > max_w:
                if self._power_limit_high_since is None:
                    self._power_limit_high_since = now
                elif (now - self._power_limit_high_since).total_seconds() >= POWER_LIMIT_SPIKE_SEC:
                    _LOGGER.warning(
                        "%s: [power limit] spegnimento (consumo=%.0fW > max=%.0fW)",
                        self._attr_name, consumo, max_w,
                    )
                    await self.hass.services.async_call("climate", "turn_off", {"entity_id": self._climate_entity}, blocking=True)
                    self._power_limit_off = True
                    self._power_limit_off_at = now
                    self._power_limit_high_since = None
                    self._power_limit_low_since = None
                    # Registra in coordinamento per cascata multi
                    coord = self.hass.data.setdefault(DOMAIN, {}).setdefault("_coordination", {})
                    pl_order = coord.setdefault("power_limit_off_order", [])
                    if self.entry.entry_id not in pl_order:
                        pl_order.append(self.entry.entry_id)
                    await self._async_power_limit_notify(is_on=False, consumo=consumo)
                    return
            else:
                self._power_limit_high_since = None

        # --- Riaccensione dopo calo consumo ---
        if self._power_limit_off:
            restore_threshold = max_w - hysteresis_w
            if consumo <= restore_threshold:
                if self._power_limit_low_since is None:
                    self._power_limit_low_since = now
                elif (now - self._power_limit_low_since) >= timedelta(minutes=restore_min):
                    # Modalità multi: rispetta cascata e stagger
                    if mode == POWER_LIMIT_MODE_MULTI:
                        coord = self.hass.data.setdefault(DOMAIN, {}).setdefault("_coordination", {})
                        pl_order = coord.get("power_limit_off_order", [])
                        last_restore = coord.get("last_power_limit_restore")
                        # Riaccende solo se siamo il primo della lista e lo stagger è passato
                        if pl_order and pl_order[-1] == self.entry.entry_id:
                            if last_restore is None or (now - last_restore) >= timedelta(minutes=POWER_LIMIT_RESTORE_STAGGER_MIN):
                                # Verifica che il consumo sia ancora sotto soglia
                                if consumo <= restore_threshold:
                                    await self._async_power_limit_restore()
                                    pl_order.pop()
                                    coord["last_power_limit_restore"] = now
                        return
                    else:
                        # Modalità unico: riaccende direttamente
                        await self._async_power_limit_restore()
            else:
                self._power_limit_low_since = None

    async def _async_power_limit_restore(self) -> None:
        """Riaccende il clima dopo calo consumo."""
        _LOGGER.info("%s: [power limit] riaccensione dopo calo consumo", self._attr_name)
        await self.hass.services.async_call("climate", "turn_on", {"entity_id": self._climate_entity}, blocking=True)
        self._power_limit_off = False
        self._power_limit_off_at = None
        self._power_limit_low_since = None
        self._power_limit_high_since = None
        await self._async_power_limit_notify(is_on=True)

    async def _async_power_limit_notify(self, is_on: bool, consumo: float = 0) -> None:
        """Notifica spegnimento/riaccensione per protezione potenza."""
        notify_tts = bool(get_conf(self.entry, CONF_POWER_LIMIT_NOTIFY_TTS, DEFAULT_POWER_LIMIT_NOTIFY_TTS))
        notify_tel = bool(get_conf(self.entry, CONF_POWER_LIMIT_NOTIFY_TELEGRAM, DEFAULT_POWER_LIMIT_NOTIFY_TELEGRAM))
        if not notify_tts and not notify_tel:
            return

        config_mode = get_conf(self.entry, CONF_CONFIG_MODE, CONFIG_MODE_FULL)
        if is_on:
            if config_mode == CONFIG_MODE_FULL:
                tpl = get_conf(self.entry, CONF_POWER_LIMIT_MSG_ON, DEFAULT_POWER_LIMIT_MSG_ON)
            else:
                tpl = DEFAULT_POWER_LIMIT_MSG_ON
        else:
            if config_mode == CONFIG_MODE_FULL:
                tpl = get_conf(self.entry, CONF_POWER_LIMIT_MSG_OFF, DEFAULT_POWER_LIMIT_MSG_OFF)
            else:
                tpl = DEFAULT_POWER_LIMIT_MSG_OFF

        message = await self._async_render(tpl, {"name": self._attr_name, "consumo": round(consumo)})

        if notify_tts:
            await self._async_speak(message, bypass_quiet=True)
        if notify_tel:
            await self._async_send_notification(message, bypass_quiet=True)

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

        # Nel modo semplificato la notifica fine notte è gestita da
        # _async_simple_notify_night_end — non inviare duplicati
        mode = self._get_config_mode()
        if mode not in (CONFIG_MODE_SIMPLE, CONFIG_MODE_SIMPLE_FV):
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
            mode = self._get_config_mode()
            if mode in (CONFIG_MODE_SIMPLE, CONFIG_MODE_SIMPLE_FV):
                await self._async_simple_notify_temp_change(temp, target)
            else:
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
        mode = self._get_config_mode()
        is_simple = mode in (CONFIG_MODE_SIMPLE, CONFIG_MODE_SIMPLE_FV)
        real_state = self.hass.states.get(self._climate_entity)
        ac_was_on = bool(real_state and real_state.state in ("cool", "dry"))

        if self._is_real_transition(old_state, new_state, "off", "on"):
            if self._window_cancel_timer is not None:
                self._window_cancel_timer()
                self._window_cancel_timer = None
            if is_simple:
                await self._async_simple_notify_window(True, SIMPLE_WINDOW_DELAY_MIN, ac_was_on)
                await self._async_window_opened_simple()
            else:
                await self._async_window_opened()
        elif self._is_real_transition(old_state, new_state, "on", "off"):
            if self._window_cancel_timer is not None:
                self._window_cancel_timer()
                self._window_cancel_timer = None
            if is_simple:
                await self._async_simple_notify_window(False, 0, ac_was_on)
                await self._async_window_closed_simple()
            else:
                await self._async_window_closed()



    def _cancel_dry_timer(self, reason: str = "n/d") -> None:
        """Cancella il timer DRY→COOL e resetta le variabili di stato."""
        was_active = self._simple_dry_end is not None
        if self._dry_cancel_timer is not None:
            self._dry_cancel_timer()
            self._dry_cancel_timer = None
        self._simple_dry_end = None
        self._simple_dry_since = None
        if was_active:
            _LOGGER.warning("%s: [DRY-TRACE] timer CANCELLATO — motivo: %s", self._attr_name, reason)

    def _schedule_dry_timer(self, reason: str = "n/d") -> None:
        """Avvia il timer DRY→COOL usando async_track_point_in_time.

        Calcola il timestamp assoluto di scadenza (now + dry_max_min) e
        schedula la callback a quell'ora esatta. Al riavvio di HA, il
        timestamp viene recuperato da RestoreEntity (attributo dry_end) e
        il timer viene rischedulato — se il timestamp è già nel passato,
        HA lo fa scattare immediatamente al prossimo tick dell'event loop.
        """
        # Cancella eventuale timer precedente
        if self._dry_cancel_timer is not None:
            self._dry_cancel_timer()
            self._dry_cancel_timer = None

        now = dt_util.utcnow()
        dry_max_min = int(get_conf(self.entry, CONF_SIMPLE_DRY_MAX_MIN, DEFAULT_SIMPLE_DRY_MAX_MIN))
        dry_end = now + timedelta(minutes=dry_max_min)

        self._simple_dry_since = now
        self._simple_dry_end = dry_end

        self._dry_cancel_timer = async_track_point_in_time(
            self.hass, self._async_dry_to_cool, dry_end
        )
        _LOGGER.warning(
            "%s: [DRY-TRACE] timer AVVIATO — motivo: %s — scadrà alle %s (%s min)",
            self._attr_name, reason, dry_end.isoformat(), dry_max_min,
        )

    async def _async_dry_to_cool(self, *_) -> None:
        """Callback di async_track_point_in_time: passa da DRY a COOL.

        Se il Gree è unavailable al momento dello scatto, non fa niente —
        il fallback nel loop periodico (ogni 5 min) rileverà che dry_end
        è nel passato e completerà la transizione al ciclo successivo.
        """
        self._dry_cancel_timer = None  # già scattato, non serve più cancellare
        real_state = self.hass.states.get(self._climate_entity)
        if real_state and real_state.state == "dry":
            _LOGGER.warning("%s: [DRY-TRACE] timer scattato — passo a raffreddamento (set_hvac_mode cool)", self._attr_name)
            await self.hass.services.async_call(
                "climate", "set_hvac_mode",
                {"entity_id": self._climate_entity, "hvac_mode": "cool"},
                blocking=True,
            )
            self._simple_dry_end = None
            self._simple_dry_since = None
        elif real_state and real_state.state in ("unknown", "unavailable"):
            # Gree non raggiungibile in questo momento — il fallback del loop
            # periodico ci pensa al prossimo ciclo (dry_end rimane settato)
            _LOGGER.warning(
                "%s: [DRY→COOL] timer scattato ma Gree è %s — il fallback periodico completerà la transizione",
                self._attr_name, real_state.state,
            )
        else:
            # Clima già spento o in COOL — nessuna azione, pulisci
            _LOGGER.debug(
                "%s: [DRY→COOL] timer scattato ma stato=%s — nessuna azione",
                self._attr_name, real_state.state if real_state else "None",
            )
            self._simple_dry_end = None
            self._simple_dry_since = None

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

    async def _async_window_closed_simple(self) -> None:
        """Chiusura finestra in modo semplificato — ripristina clima senza notifiche duplicate."""
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
        # Debounce 1 secondo — ignora rimbalzi sensore reed
        if hasattr(self, '_door_debounce_cancel') and self._door_debounce_cancel:
            self._door_debounce_cancel()
            self._door_debounce_cancel = None
        _new_state = new_state
        _old_state = old_state
        async def _process_door(_now=None):
            self._door_debounce_cancel = None
            current = self.hass.states.get(self._door_sensor)
            if current is None or current.state != _new_state.state:
                return
            await self._async_handle_door_debounced(_new_state, _old_state)
        self._door_debounce_cancel = async_call_later(
            self.hass, timedelta(seconds=1),
            _process_door
        )

    async def _async_handle_door_debounced(self, new_state: State | None, old_state: State | None) -> None:
        """Gestisce l'evento porta dopo il debounce di 1 secondo."""
        mode = self._get_config_mode()
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
