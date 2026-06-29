"""Utility condivise per il Termostato Intelligente FV."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry


def get_conf(entry: ConfigEntry, key: str, default=None):
    """Legge un valore dalla configurazione dell'entry con fallback al default."""
    val = entry.data.get(key)
    if val is None:
        val = entry.options.get(key, default)
    return val
