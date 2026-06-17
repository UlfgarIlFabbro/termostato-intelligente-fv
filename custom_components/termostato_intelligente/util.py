"""Funzioni di utilità condivise dall'integrazione."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry


def get_conf(entry: ConfigEntry, key: str, default: Any = None) -> Any:
    """Legge un valore di configurazione.

    Priorità: opzioni (modificabili da Impostazioni > Integrazioni > Opzioni)
    poi i dati impostati alla creazione, poi il default passato.
    Tratta stringhe vuote / liste vuote come "non impostato".
    """
    value = entry.options.get(key)
    if value not in (None, "", []):
        return value
    value = entry.data.get(key)
    if value not in (None, "", []):
        return value
    return default
