"""Integrazione Termostato Intelligente FV + Batteria + Finestra + Presenza."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    DEFAULT_EMERGENCY_HEAT_END_THRESHOLD,
    DEFAULT_EMERGENCY_HEAT_THRESHOLD,
    DEFAULT_EMERGENCY_NOTIFY_TELEGRAM,
    DEFAULT_EMERGENCY_NOTIFY_TTS,
    DEFAULT_FV_MARGIN_W,
    DEFAULT_FV_PRIORITY,
    DEFAULT_FV_SHUTOFF_DELAY_MIN,
    DEFAULT_FV_SHUTOFF_ENABLED,
    DEFAULT_FV_SHUTOFF_THRESHOLD,
    DEFAULT_FV_STAGGER_MIN,
    DEFAULT_NIGHT_END_SHUTOFF_AUTO_ONLY,
    DEFAULT_NIGHT_END_SHUTOFF_ENABLED,
    DEFAULT_POWER_LIMIT_ENABLED,
    DEFAULT_POWER_LIMIT_HYSTERESIS_W,
    DEFAULT_POWER_LIMIT_MAX_W,
    DEFAULT_POWER_LIMIT_MODE,
    DEFAULT_POWER_LIMIT_NOTIFY_TELEGRAM,
    DEFAULT_POWER_LIMIT_NOTIFY_TTS,
    DEFAULT_POWER_LIMIT_RESTORE_MIN,
    DEFAULT_SIMPLE_DRY_ENABLED,
    DEFAULT_SIMPLE_DRY_MAX_MIN,
    DEFAULT_SIMPLE_NIGHT_END,
    DEFAULT_SIMPLE_NIGHT_START,
    DEFAULT_SIMPLE_NO_AUTO_ON_NIGHT,
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
    DEFAULT_SIMPLE_SUNSET_ANTICIPATE_H,
    DEFAULT_SIMPLE_TARGET_DAY,
    DEFAULT_SIMPLE_TARGET_NIGHT,
    DEFAULT_SIMPLE_TURN_ON_OFFSET_EXT,
    DEFAULT_SOC_MIN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SWITCH]
SCHEMA_VERSION = 2
VALID_MODES = ("simple", "simple_fv", "full")

_FIELD_DEFAULTS = {
    "simple_notify_tel_ac_on": DEFAULT_SIMPLE_NOTIFY_TEL_AC_ON,
    "simple_notify_tel_ac_off": DEFAULT_SIMPLE_NOTIFY_TEL_AC_OFF,
    "simple_notify_tel_temp_change": DEFAULT_SIMPLE_NOTIFY_TEL_TEMP_CHANGE,
    "simple_notify_tel_window_open": DEFAULT_SIMPLE_NOTIFY_TEL_WINDOW_OPEN,
    "simple_notify_tel_window_close": DEFAULT_SIMPLE_NOTIFY_TEL_WINDOW_CLOSE,
    "simple_notify_tel_door_open": DEFAULT_SIMPLE_NOTIFY_TEL_DOOR_OPEN,
    "simple_notify_tel_door_close": DEFAULT_SIMPLE_NOTIFY_TEL_DOOR_CLOSE,
    "simple_notify_tel_night_start": DEFAULT_SIMPLE_NOTIFY_TEL_NIGHT_START,
    "simple_notify_tel_night_end": DEFAULT_SIMPLE_NOTIFY_TEL_NIGHT_END,
    "simple_notify_tts_ac_on": DEFAULT_SIMPLE_NOTIFY_TTS_AC_ON,
    "simple_notify_tts_ac_off": DEFAULT_SIMPLE_NOTIFY_TTS_AC_OFF,
    "simple_notify_tts_temp_change": DEFAULT_SIMPLE_NOTIFY_TTS_TEMP_CHANGE,
    "simple_notify_tts_window_open": DEFAULT_SIMPLE_NOTIFY_TTS_WINDOW_OPEN,
    "simple_notify_tts_window_close": DEFAULT_SIMPLE_NOTIFY_TTS_WINDOW_CLOSE,
    "simple_notify_tts_door_open": DEFAULT_SIMPLE_NOTIFY_TTS_DOOR_OPEN,
    "simple_notify_tts_door_close": DEFAULT_SIMPLE_NOTIFY_TTS_DOOR_CLOSE,
    "simple_notify_tts_night_start": DEFAULT_SIMPLE_NOTIFY_TTS_NIGHT_START,
    "simple_notify_tts_night_end": DEFAULT_SIMPLE_NOTIFY_TTS_NIGHT_END,
    "simple_quiet_night_tts": DEFAULT_SIMPLE_QUIET_NIGHT_TTS,
    "simple_quiet_night_notify": DEFAULT_SIMPLE_QUIET_NIGHT_NOTIFY,
    "simple_no_auto_on_night": DEFAULT_SIMPLE_NO_AUTO_ON_NIGHT,
    "simple_turn_on_offset": DEFAULT_SIMPLE_TURN_ON_OFFSET_EXT,
    "simple_dry_enabled": DEFAULT_SIMPLE_DRY_ENABLED,
    "simple_dry_max_min": DEFAULT_SIMPLE_DRY_MAX_MIN,
    "simple_target_day": DEFAULT_SIMPLE_TARGET_DAY,
    "simple_target_night": DEFAULT_SIMPLE_TARGET_NIGHT,
    "simple_night_start": DEFAULT_SIMPLE_NIGHT_START,
    "simple_night_end": DEFAULT_SIMPLE_NIGHT_END,
    "simple_sunset_anticipate_h": DEFAULT_SIMPLE_SUNSET_ANTICIPATE_H,
    "night_end_shutoff_enabled": DEFAULT_NIGHT_END_SHUTOFF_ENABLED,
    "night_end_shutoff_auto_only": DEFAULT_NIGHT_END_SHUTOFF_AUTO_ONLY,
    "update_interval": 1,
    "fv_margin_w": DEFAULT_FV_MARGIN_W,
    "fv_priority": DEFAULT_FV_PRIORITY,
    "fv_shutoff_delay_min": DEFAULT_FV_SHUTOFF_DELAY_MIN,
    "fv_shutoff_enabled": DEFAULT_FV_SHUTOFF_ENABLED,
    "fv_shutoff_threshold": DEFAULT_FV_SHUTOFF_THRESHOLD,
    "fv_stagger_minutes": DEFAULT_FV_STAGGER_MIN,
    "soc_min": DEFAULT_SOC_MIN,
    "power_limit_enabled": DEFAULT_POWER_LIMIT_ENABLED,
    "power_limit_mode": DEFAULT_POWER_LIMIT_MODE,
    "power_limit_max_w": DEFAULT_POWER_LIMIT_MAX_W,
    "power_limit_hysteresis_w": DEFAULT_POWER_LIMIT_HYSTERESIS_W,
    "power_limit_restore_min": DEFAULT_POWER_LIMIT_RESTORE_MIN,
    "power_limit_notify_tts": DEFAULT_POWER_LIMIT_NOTIFY_TTS,
    "power_limit_notify_telegram": DEFAULT_POWER_LIMIT_NOTIFY_TELEGRAM,
    "emergency_heat_threshold": DEFAULT_EMERGENCY_HEAT_THRESHOLD,
    "emergency_heat_end_threshold": DEFAULT_EMERGENCY_HEAT_END_THRESHOLD,
    "emergency_notify_tts": DEFAULT_EMERGENCY_NOTIFY_TTS,
    "emergency_notify_telegram": DEFAULT_EMERGENCY_NOTIFY_TELEGRAM,
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configura una entry. NON chiama async_update_entry per evitare loop."""
    hass.data.setdefault(DOMAIN, {}).setdefault(entry.entry_id, {})
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Rimuove una entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migra le entry — scatta solo quando version < SCHEMA_VERSION.
    
    TABELLA CONVERSIONE config_mode:
    - None / "semplificato" / "semplificato_fv" / qualsiasi valore non valido:
      → "simple_fv" se fv_sensor presente, altrimenti "simple"
    - "simple" / "simple_fv" / "full": mantieni invariato
    
    NON chiama async_update_entry dentro async_setup_entry per evitare loop.
    """
    _LOGGER.info(
        "Migrazione %s v%s → v%s",
        config_entry.title,
        config_entry.version,
        SCHEMA_VERSION,
    )

    new_data = dict(config_entry.data)

    # TABELLA CONVERSIONE config_mode
    current_mode = new_data.get("config_mode")
    if current_mode not in VALID_MODES:
        new_data["config_mode"] = "simple_fv" if new_data.get("fv_sensor") else "simple"
        _LOGGER.info(
            "%s: config_mode '%s' → '%s'",
            config_entry.title,
            current_mode,
            new_data["config_mode"],
        )

    # Aggiunge solo i campi MANCANTI — non sovrascrive mai
    for key, default in _FIELD_DEFAULTS.items():
        if key not in new_data:
            new_data[key] = default

    hass.config_entries.async_update_entry(
        config_entry,
        data=new_data,
        version=SCHEMA_VERSION,
    )
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Ricarica l'integrazione quando le opzioni vengono modificate dall'utente."""
    await hass.config_entries.async_reload(entry.entry_id)
