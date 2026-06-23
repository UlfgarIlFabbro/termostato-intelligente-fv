"""Costanti per l'integrazione Termostato Intelligente FV."""

DOMAIN = "termostato_intelligente"

# --- Entità core ---
CONF_NAME = "name"
CONF_CLIMATE_ENTITY = "climate_entity"
CONF_TEMP_SENSOR = "temp_sensor"
CONF_WINDOW_SENSOR = "window_sensor"
CONF_PRESENCE_SENSOR = "presence_sensor"
CONF_DOOR_SENSOR = "door_sensor"

# --- Energia (FV / batteria) ---
CONF_FV_SENSOR = "fv_sensor"
CONF_CONSUMPTION_SENSOR = "consumption_sensor"
CONF_BATTERY_SENSOR = "battery_sensor"
CONF_FV_MARGIN_W = "fv_margin_w"
CONF_SOC_MIN = "soc_min"
CONF_FV_START_TIME = "fv_start_time"
CONF_FV_END_TIME = "fv_end_time"
CONF_FV_PRIORITY = "fv_priority"
CONF_FV_STAGGER_MIN = "fv_stagger_minutes"

# --- Spegnimento diurno da FV ---
CONF_FV_SHUTOFF_ENABLED = "fv_shutoff_enabled"
CONF_FV_SHUTOFF_DELAY_MIN = "fv_shutoff_delay_min"
CONF_FV_SHUTOFF_EXTRA_HOURS = "fv_shutoff_extra_hours"

# --- Profilo di regolazione ---
CONF_PROFILE = "profile"
PRESET_BILANCIATO = "bilanciato"
PRESET_AGGRESSIVO = "aggressivo"
PRESET_DELICATO = "delicato"
PRESET_PERSONALIZZATO = "personalizzato"
DEFAULT_PROFILE = PRESET_BILANCIATO

# --- Soglie termiche / timing ---
CONF_TARGET_TEMP_DEFAULT = "target_temp_default"
CONF_EXTREME_OFFSET = "extreme_offset"
CONF_HOT_OFFSET = "hot_offset"
CONF_RANGE_OFFSET = "range_offset"
CONF_BELOW_OFFSET = "below_offset"
CONF_TURN_ON_OFFSET = "turn_on_offset"
CONF_TEMP_DELTA = "temp_delta"
CONF_EXTREME_DELTA = "extreme_delta"
CONF_PRESENCE_BOOST_ENABLED = "presence_boost_enabled"
CONF_PRESENCE_BOOST_MIN = "presence_boost_minutes"
CONF_PRESENCE_BOOST_OFFSET = "presence_boost_offset"
CONF_WINDOW_DELAY_MIN = "window_delay_minutes"
CONF_UPDATE_INTERVAL_MIN = "update_interval_minutes"

# --- Calibrazione sonda interna climatizzatore ---
CONF_CALIBRATION_MAX_OFFSET = "calibration_max_offset"
CONF_MIN_BELOW_INTERNAL = "min_below_internal"

# --- Modalità notturna ---
CONF_NIGHT_START_TIME = "night_start_time"
CONF_NIGHT_END_TIME = "night_end_time"
CONF_NIGHT_OFFSET = "night_offset"
CONF_NIGHT_TURN_ON_OFFSET = "night_turn_on_offset"
CONF_NIGHT_AC_ENABLED = "night_ac_enabled"

# --- Spegnimento notturno per raggiungimento target ---
CONF_NIGHT_SHUTOFF_ENABLED = "night_shutoff_enabled"
CONF_NIGHT_SHUTOFF_DELTA = "night_shutoff_delta"
CONF_NIGHT_SHUTOFF_MIN = "night_shutoff_min"

# --- Notifiche TTS (Google / media_player) ---
CONF_TTS_PLAYERS = "tts_media_players"
CONF_TTS_ENGINE = "tts_engine_entity"
CONF_TTS_MESSAGE_OPEN = "tts_message_open"

# --- Notifiche Telegram / notify ---
CONF_NOTIFY_TARGETS = "notify_targets"
CONF_NOTIFY_CHAT_IDS = "notify_chat_ids"
CONF_NOTIFY_MESSAGE = "notify_message"
CONF_NOTIFY_TEMP_CHANGE_ENABLED = "notify_temp_change_enabled"
CONF_NOTIFY_TEMP_CHANGE_MESSAGE = "notify_temp_change_message"

# --- Avvisi accensione/spegnimento automatico ---
# Abilitazione per canale
CONF_NOTIFY_POWER_TTS = "notify_power_tts"      # voce Google Home
CONF_NOTIFY_POWER_NOTIFY = "notify_power_notify"  # Telegram / notify

# --- Fascia di silenzio (nessun avviso in queste ore) ---
# I due canali (TTS e notify) possono essere silenziati indipendentemente.
CONF_QUIET_ENABLED = "quiet_enabled"
CONF_QUIET_START_TIME = "quiet_start_time"
CONF_QUIET_END_TIME = "quiet_end_time"
CONF_QUIET_TTS = "quiet_tts"       # silenzia la voce nella fascia
CONF_QUIET_NOTIFY = "quiet_notify"  # silenzia Telegram nella fascia

# --- Avviso porta (selettivo per canale) ---
CONF_DOOR_ALERT_ENABLED = "door_alert_enabled"
CONF_DOOR_ALERT_MESSAGE = "door_alert_message"
CONF_DOOR_ALERT_TTS = "door_alert_tts"
CONF_DOOR_ALERT_NOTIFY = "door_alert_notify"

# --- Switch ausiliari ---
SWITCH_KEY_MASTER = "switch_master"
SWITCH_KEY_FV = "switch_fv"
SWITCH_KEY_QUICK = "switch_quick"

# --- Motivi di accensione/spegnimento (usati nei messaggi) ---
REASON_FV = "fv"
REASON_NIGHT = "night"
REASON_NIGHT_SHUTOFF = "night_shutoff"
REASON_FV_SHUTOFF = "fv_shutoff"
REASON_WINDOW = "window"

# --- Default ---
DEFAULT_NAME = "Termostato Intelligente"
DEFAULT_TARGET_TEMP = 25.0
DEFAULT_EXTREME_OFFSET = 2.0
DEFAULT_HOT_OFFSET = 1.5
DEFAULT_RANGE_OFFSET = 0.2
DEFAULT_BELOW_OFFSET = 0.1
DEFAULT_TURN_ON_OFFSET = 0.8
DEFAULT_TEMP_DELTA = 1.0
DEFAULT_EXTREME_DELTA = 2.0
DEFAULT_PRESENCE_BOOST_ENABLED = True
DEFAULT_FV_MARGIN_W = 1200
DEFAULT_SOC_MIN = 70
DEFAULT_FV_START_TIME = "10:00:00"
DEFAULT_FV_END_TIME = "16:00:00"
DEFAULT_FV_PRIORITY = 50
DEFAULT_FV_STAGGER_MIN = 5
DEFAULT_FV_SHUTOFF_ENABLED = False
DEFAULT_FV_SHUTOFF_DELAY_MIN = 5
DEFAULT_FV_SHUTOFF_EXTRA_HOURS = 1.0
DEFAULT_PRESENCE_BOOST_MIN = 10
DEFAULT_PRESENCE_BOOST_OFFSET = 1.0
DEFAULT_WINDOW_DELAY_MIN = 5
DEFAULT_UPDATE_INTERVAL_MIN = 5
DEFAULT_CALIBRATION_MAX_OFFSET = 3.0
DEFAULT_MIN_BELOW_INTERNAL = 1.0
DEFAULT_NIGHT_START_TIME = "23:00:00"
DEFAULT_NIGHT_END_TIME = "07:00:00"
DEFAULT_NIGHT_OFFSET = 0.0
DEFAULT_NIGHT_TURN_ON_OFFSET = 1.5
DEFAULT_NIGHT_AC_ENABLED = False
DEFAULT_NIGHT_SHUTOFF_ENABLED = False
DEFAULT_NIGHT_SHUTOFF_DELTA = 0.3
DEFAULT_NIGHT_SHUTOFF_MIN = 30
DEFAULT_NOTIFY_TEMP_CHANGE_ENABLED = True
DEFAULT_DOOR_ALERT_ENABLED = False
DEFAULT_DOOR_ALERT_TTS = True
DEFAULT_DOOR_ALERT_NOTIFY = True
DEFAULT_NOTIFY_POWER_TTS = False
DEFAULT_NOTIFY_POWER_NOTIFY = True
DEFAULT_QUIET_ENABLED = False
DEFAULT_QUIET_START_TIME = "23:00:00"
DEFAULT_QUIET_END_TIME = "07:00:00"
DEFAULT_QUIET_TTS = True
DEFAULT_QUIET_NOTIFY = False

DEFAULT_TTS_MESSAGE_OPEN = (
    "Finestra aperta, chiudila o spengo il climatizzatore tra {{ delay }} minuti"
)
DEFAULT_NOTIFY_MESSAGE = "{{ name }}: finestra aperta, clima spento"
DEFAULT_NOTIFY_TEMP_CHANGE_MESSAGE = (
    "{{ name }}: climatizzatore impostato a {{ new_temp }}°C "
    "(ventola {{ fan_mode }}) - stanza {{ room_temp }}°C, target {{ target }}°C"
)
DEFAULT_DOOR_ALERT_MESSAGE = "{{ name }}: porta aperta"

# Messaggi accensione automatica (per motivo)
DEFAULT_POWER_ON_FV_MESSAGE = (
    "{{ name }}: ho acceso il climatizzatore perché stai producendo "
    "{{ fv }}W di fotovoltaico e la temperatura della stanza è {{ temp }}°C "
    "(target {{ target }}°C)"
)
DEFAULT_POWER_ON_NIGHT_MESSAGE = (
    "{{ name }}: ho acceso il climatizzatore in modalità notturna perché "
    "la stanza è a {{ temp }}°C (target notte {{ target }}°C)"
)
DEFAULT_POWER_OFF_FV_MESSAGE = (
    "{{ name }}: ho spento il climatizzatore perché la produzione fotovoltaica "
    "è scesa sotto il consumo attuale ({{ fv }}W vs {{ consumo }}W)"
)
DEFAULT_POWER_OFF_NIGHT_MESSAGE = (
    "{{ name }}: ho spento il climatizzatore perché la stanza "
    "ha raggiunto la temperatura target notturna ({{ temp }}°C ≤ {{ target }}°C)"
)

# Limite volontario: il climatizzatore va pilotato solo su questi fan_mode
FAN_MODES_ALLOWED = ["low", "medium", "high"]

PRESET_VALUES: dict[str, dict[str, float]] = {
    PRESET_BILANCIATO: {
        CONF_EXTREME_OFFSET: 2.0,
        CONF_HOT_OFFSET: 1.5,
        CONF_RANGE_OFFSET: 0.2,
        CONF_BELOW_OFFSET: 0.1,
        CONF_TEMP_DELTA: 1.0,
        CONF_EXTREME_DELTA: 2.0,
        CONF_CALIBRATION_MAX_OFFSET: 3.0,
        CONF_MIN_BELOW_INTERNAL: 1.0,
        CONF_TURN_ON_OFFSET: 0.8,
    },
    PRESET_AGGRESSIVO: {
        CONF_EXTREME_OFFSET: 1.5,
        CONF_HOT_OFFSET: 1.0,
        CONF_RANGE_OFFSET: 0.1,
        CONF_BELOW_OFFSET: 0.1,
        CONF_TEMP_DELTA: 1.5,
        CONF_EXTREME_DELTA: 3.0,
        CONF_CALIBRATION_MAX_OFFSET: 4.0,
        CONF_MIN_BELOW_INTERNAL: 1.5,
        CONF_TURN_ON_OFFSET: 0.5,
    },
    PRESET_DELICATO: {
        CONF_EXTREME_OFFSET: 3.0,
        CONF_HOT_OFFSET: 2.0,
        CONF_RANGE_OFFSET: 0.4,
        CONF_BELOW_OFFSET: 0.2,
        CONF_TEMP_DELTA: 0.5,
        CONF_EXTREME_DELTA: 1.5,
        CONF_CALIBRATION_MAX_OFFSET: 2.0,
        CONF_MIN_BELOW_INTERNAL: 0.5,
        CONF_TURN_ON_OFFSET: 1.2,
    },
}
