"""Piattaforma climate: il vero e proprio 'termostato intelligente'."""

from __future__ import annotations

import logging
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
    FAN_MODES_ALLOWED,
)
from .util import get_conf

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crea l'unica entità climate per questa istanza configurata."""
    async_add_entities([SmartFvClimate(hass, entry)])


class SmartFvClimate(ClimateEntity, RestoreEntity):
    """Termostato intelligente: pilota un climatizzatore reale.

    Logica riprodotta dalle automazioni originali:
    - blocco totale se la finestra è aperta
    - accensione solo con surplus FV (fascia oraria configurabile)
    - regolazione temperatura/fan a 3 livelli (caldo forte / sopra target / in range)
    - fan limitato a low/medium
    - boost presenza dopo N minuti continuativi
    - snapshot/restore + avviso TTS + notifica alla finestra
    """

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
        self._fv_sensor: str | None = get_conf(entry, CONF_FV_SENSOR)
        self._consumption_sensor: str | None = get_conf(entry, CONF_CONSUMPTION_SENSOR)
        self._battery_sensor: str | None = get_conf(entry, CONF_BATTERY_SENSOR)

        self._target_temperature: float = float(
            get_conf(entry, CONF_TARGET_TEMP_DEFAULT, DEFAULT_TARGET_TEMP)
        )

        self._snapshot: dict[str, Any] | None = None
        self._window_cancel_timer = None
        self._presence_since: datetime | None = None

    # ------------------------------------------------------------------
    # Proprietà esposte (mirror del climatizzatore reale dove sensato)
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
            "snapshot_attivo": self._snapshot is not None,
            "presenza_da": self._presence_since.isoformat()
            if self._presence_since
            else None,
            "climatizzatore_reale": self._climate_entity,
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

        interval_min = int(
            get_conf(self.entry, CONF_UPDATE_INTERVAL_MIN, DEFAULT_UPDATE_INTERVAL_MIN)
        )
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._async_periodic_update, timedelta(minutes=interval_min)
            )
        )

        tracked = [
            e
            for e in (
                self._climate_entity,
                self._temp_sensor,
                self._window_sensor,
                self._presence_sensor,
            )
            if e
        ]
        if tracked:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, tracked, self._async_on_state_change
                )
            )

    async def _async_on_state_change(self, event: Event) -> None:
        entity_id = event.data.get("entity_id")
        new_state: State | None = event.data.get("new_state")
        old_state: State | None = event.data.get("old_state")

        if entity_id == self._window_sensor:
            await self._async_handle_window(new_state, old_state)
        elif entity_id == self._presence_sensor:
            if new_state and new_state.state == "on":
                if old_state is None or old_state.state != "on":
                    self._presence_since = new_state.last_changed
            else:
                self._presence_since = None

        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        """Annulla un eventuale timer finestra pendente per evitare leak/azioni a entità rimossa."""
        if self._window_cancel_timer is not None:
            self._window_cancel_timer()
            self._window_cancel_timer = None

    # ------------------------------------------------------------------
    # Comandi utente sull'entità "termostato intelligente"
    # ------------------------------------------------------------------

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        self._target_temperature = float(temperature)
        self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        if fan_mode not in FAN_MODES_ALLOWED:
            _LOGGER.warning(
                "%s: fan_mode '%s' non consentito (solo %s), uso '%s'",
                self._attr_name,
                fan_mode,
                FAN_MODES_ALLOWED,
                FAN_MODES_ALLOWED[0],
            )
            fan_mode = FAN_MODES_ALLOWED[0]
        await self.hass.services.async_call(
            "climate",
            "set_fan_mode",
            {"entity_id": self._climate_entity, "fan_mode": fan_mode},
            blocking=True,
        )
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        service = "turn_on" if hvac_mode == HVACMode.COOL else "turn_off"
        await self.hass.services.async_call(
            "climate", service, {"entity_id": self._climate_entity}, blocking=True
        )
        self.async_write_ha_state()

    # ------------------------------------------------------------------
    # Logica periodica (FV + termica + presenza)
    # ------------------------------------------------------------------

    async def _async_periodic_update(self, now: datetime | None = None) -> None:
        if not self._within_active_window():
            return
        if self._is_window_open():
            return

        temp = self.current_temperature
        if temp is None:
            return
        target = self._target_temperature

        await self._async_handle_fv_turn_on(temp, target)
        await self._async_handle_thermal(temp, target)
        await self._async_handle_presence_boost(temp, target)
        self.async_write_ha_state()

    def _within_active_window(self) -> bool:
        start_str = get_conf(self.entry, CONF_FV_START_TIME, DEFAULT_FV_START_TIME)
        end_str = get_conf(self.entry, CONF_FV_END_TIME, DEFAULT_FV_END_TIME)
        try:
            start = dt_time.fromisoformat(str(start_str))
            end = dt_time.fromisoformat(str(end_str))
        except ValueError:
            return True
        now_t = dt_util.now().time()
        if start <= end:
            return start <= now_t <= end
        return now_t >= start or now_t <= end

    def _is_window_open(self) -> bool:
        if not self._window_sensor:
            return False
        state = self.hass.states.get(self._window_sensor)
        return bool(state and state.state == "on")

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

    async def _async_handle_fv_turn_on(self, temp: float, target: float) -> None:
        if not (self._fv_sensor and self._consumption_sensor and self._battery_sensor):
            return
        if self.hvac_mode != HVACMode.OFF:
            return

        fv = self._read_float(self._fv_sensor)
        consumo = self._read_float(self._consumption_sensor)
        soc = self._read_float(self._battery_sensor)
        if fv is None or consumo is None or soc is None:
            return

        margin = float(get_conf(self.entry, CONF_FV_MARGIN_W, DEFAULT_FV_MARGIN_W))
        soc_min = float(get_conf(self.entry, CONF_SOC_MIN, DEFAULT_SOC_MIN))
        turn_on_offset = float(
            get_conf(self.entry, CONF_TURN_ON_OFFSET, DEFAULT_TURN_ON_OFFSET)
        )

        if fv > consumo + margin and soc > soc_min and temp > target + turn_on_offset:
            await self.hass.services.async_call(
                "climate", "turn_on", {"entity_id": self._climate_entity}, blocking=True
            )

    async def _async_handle_thermal(self, temp: float, target: float) -> None:
        extreme_offset = float(
            get_conf(self.entry, CONF_EXTREME_OFFSET, DEFAULT_EXTREME_OFFSET)
        )
        hot_offset = float(get_conf(self.entry, CONF_HOT_OFFSET, DEFAULT_HOT_OFFSET))
        range_offset = float(
            get_conf(self.entry, CONF_RANGE_OFFSET, DEFAULT_RANGE_OFFSET)
        )
        below_offset = float(
            get_conf(self.entry, CONF_BELOW_OFFSET, DEFAULT_BELOW_OFFSET)
        )
        delta = float(get_conf(self.entry, CONF_TEMP_DELTA, DEFAULT_TEMP_DELTA))
        extreme_delta = float(
            get_conf(self.entry, CONF_EXTREME_DELTA, DEFAULT_EXTREME_DELTA)
        )

        # 5 fasce, in ordine dalla più calda alla più fredda:
        #   > extreme_offset       -> caldo estremo: target-extreme_delta, ventola alta
        #   > hot_offset           -> caldo forte:   target-delta,         ventola media
        #   > range_offset         -> caldo:         target-delta,         ventola bassa
        #   > -below_offset        -> vicino target: target,               ventola bassa
        #   altrimenti             -> sotto target:  target+delta,         ventola bassa
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

        real_state = self.hass.states.get(self._climate_entity)
        current_temp = real_state.attributes.get("temperature") if real_state else None
        current_fan = real_state.attributes.get("fan_mode") if real_state else None

        if current_temp is None or abs(float(current_temp) - new_temp) > 0.01:
            await self.hass.services.async_call(
                "climate",
                "set_temperature",
                {"entity_id": self._climate_entity, "temperature": new_temp},
                blocking=True,
            )
        if current_fan != fan_mode:
            await self.hass.services.async_call(
                "climate",
                "set_fan_mode",
                {"entity_id": self._climate_entity, "fan_mode": fan_mode},
                blocking=True,
            )

    async def _async_handle_presence_boost(self, temp: float, target: float) -> None:
        if not self._presence_sensor or self._presence_since is None:
            return
        if not bool(
            get_conf(self.entry, CONF_PRESENCE_BOOST_ENABLED, DEFAULT_PRESENCE_BOOST_ENABLED)
        ):
            return

        boost_minutes = int(
            get_conf(self.entry, CONF_PRESENCE_BOOST_MIN, DEFAULT_PRESENCE_BOOST_MIN)
        )
        boost_offset = float(
            get_conf(self.entry, CONF_PRESENCE_BOOST_OFFSET, DEFAULT_PRESENCE_BOOST_OFFSET)
        )
        elapsed = dt_util.utcnow() - self._presence_since
        if (
            elapsed >= timedelta(minutes=boost_minutes)
            and temp > target + boost_offset
            and self.fan_mode != "medium"
        ):
            await self.hass.services.async_call(
                "climate",
                "set_fan_mode",
                {"entity_id": self._climate_entity, "fan_mode": "medium"},
                blocking=True,
            )

    # ------------------------------------------------------------------
    # Gestione finestra: snapshot, avviso TTS, spegnimento ritardato, restore
    # ------------------------------------------------------------------

    async def _async_handle_window(
        self, new_state: State | None, old_state: State | None
    ) -> None:
        if new_state is None:
            return

        if self._window_cancel_timer is not None:
            self._window_cancel_timer()
            self._window_cancel_timer = None

        if new_state.state == "on":
            await self._async_window_opened()
        else:
            await self._async_window_closed()

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

        delay_min = int(
            get_conf(self.entry, CONF_WINDOW_DELAY_MIN, DEFAULT_WINDOW_DELAY_MIN)
        )
        await self._async_notify_tts(delay_min)

        self._window_cancel_timer = async_call_later(
            self.hass, timedelta(minutes=delay_min), self._async_window_timeout
        )

    async def _async_window_timeout(self, now: datetime | None = None) -> None:
        self._window_cancel_timer = None
        if not self._is_window_open():
            return
        await self.hass.services.async_call(
            "climate", "turn_off", {"entity_id": self._climate_entity}, blocking=True
        )
        await self._async_notify_notify()
        self.async_write_ha_state()

    async def _async_window_closed(self) -> None:
        if self._snapshot is None:
            return
        snap, self._snapshot = self._snapshot, None

        if snap["hvac_mode"] == "off":
            return

        await self.hass.services.async_call(
            "climate", "turn_on", {"entity_id": self._climate_entity}, blocking=True
        )
        if snap.get("temperature") is not None:
            await self.hass.services.async_call(
                "climate",
                "set_temperature",
                {"entity_id": self._climate_entity, "temperature": snap["temperature"]},
                blocking=True,
            )
        if snap.get("fan_mode") is not None:
            await self.hass.services.async_call(
                "climate",
                "set_fan_mode",
                {"entity_id": self._climate_entity, "fan_mode": snap["fan_mode"]},
                blocking=True,
            )

    # ------------------------------------------------------------------
    # Notifiche: TTS su dispositivi Google + notify/Telegram, personalizzabili
    # ------------------------------------------------------------------

    async def _async_render(self, template_str: str, variables: dict[str, Any]) -> str:
        try:
            tpl = Template(template_str, self.hass)
            return tpl.async_render(variables=variables, parse_result=False)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning(
                "%s: errore nel rendering del messaggio ('%s'): %s",
                self._attr_name,
                template_str,
                err,
            )
            return template_str

    async def _async_notify_tts(self, delay_min: int) -> None:
        players = get_conf(self.entry, CONF_TTS_PLAYERS, [])
        if not players:
            return

        engine = get_conf(self.entry, CONF_TTS_ENGINE)
        if not engine:
            tts_states = self.hass.states.async_all("tts")
            if not tts_states:
                _LOGGER.warning(
                    "%s: nessun motore TTS disponibile per l'avviso finestra",
                    self._attr_name,
                )
                return
            engine = tts_states[0].entity_id

        message_tpl = get_conf(self.entry, CONF_TTS_MESSAGE_OPEN, DEFAULT_TTS_MESSAGE_OPEN)
        message = await self._async_render(
            message_tpl,
            {
                "delay": delay_min,
                "name": self._attr_name,
                "target": self._target_temperature,
            },
        )

        await self.hass.services.async_call(
            "tts",
            "speak",
            {
                "entity_id": engine,
                "media_player_entity_id": players,
                "message": message,
                "cache": True,
            },
            blocking=True,
        )

    async def _async_notify_notify(self) -> None:
        targets = get_conf(self.entry, CONF_NOTIFY_TARGETS, [])
        chat_ids = get_conf(self.entry, CONF_NOTIFY_CHAT_IDS)
        if not targets and not chat_ids:
            return

        message_tpl = get_conf(self.entry, CONF_NOTIFY_MESSAGE, DEFAULT_NOTIFY_MESSAGE)
        message = await self._async_render(
            message_tpl, {"name": self._attr_name, "target": self._target_temperature}
        )

        if targets:
            await self.hass.services.async_call(
                "notify",
                "send_message",
                {"entity_id": targets, "message": message},
                blocking=True,
            )
        elif chat_ids:
            ids = [c.strip() for c in str(chat_ids).split(",") if c.strip()]
            await self.hass.services.async_call(
                "telegram_bot",
                "send_message",
                {"target": ids, "message": message},
                blocking=True,
            )
