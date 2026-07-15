// ============================================================================
// Termostato Diag Card
// Card singola entità per Termostato Intelligente FV, con sfondo colorato in
// base allo stato del climatizzatore e un pannello configurabile di attributi
// diagnostici (notte, DRY, blocco riaccensione, FV, notifiche, ecc).
// Completamente configurabile da editor grafico — nessun YAML necessario.
// ============================================================================

const STATE_COLORS = {
  cool:      { bg: "rgba(0, 0, 255, 0.5)",   border: "blue",      shadow: "rgba(0, 0, 255, 0.3)" },
  dry:       { bg: "rgba(0, 0, 255, 0.5)",   border: "lightblue", shadow: "rgba(0, 0, 255, 0.3)" },
  auto:      { bg: "rgba(255, 255, 0, 0.3)", border: "yellow",    shadow: "rgba(255, 255, 0, 0.3)" },
  fan_only:  { bg: "rgba(255, 0, 255, 0.5)", border: "violet",    shadow: "rgba(255, 0, 255, 0.3)" },
  heat:      { bg: "rgba(255, 0, 0, 0.5)",   border: "red",       shadow: "rgba(255, 0, 0, 0.3)" },
  unknown:   { bg: "rgba(0, 0, 0, 0.5)",     border: "black",     shadow: "rgba(0, 0, 0, 0.3)" },
  off:       { bg: "rgba(255, 255, 255, 0.5)", border: "black",   shadow: "rgba(255, 255, 255, 0.3)" },
};
const DEFAULT_COLOR = { bg: "rgba(255, 255, 255, 0.5)", border: "black", shadow: "rgba(255, 255, 255, 0.3)" };

function applyOpacity(rgbaString, opacity) {
  // Sostituisce solo il valore alpha di una stringa rgba() esistente,
  // mantenendo invariati i valori R/G/B — usato per rendere lo sfondo
  // della card più o meno trasparente in base alla configurazione.
  const match = rgbaString.match(/rgba?\(([^)]+)\)/);
  if (!match) return rgbaString;
  const parts = match[1].split(",").map((s) => s.trim());
  const [r, g, b] = parts;
  return `rgba(${r}, ${g}, ${b}, ${opacity})`;
}

// Elenco completo attributi diagnostici conosciuti, con etichetta e icona.
// type serve a formattare il valore: bool | timestamp | number | text | array | notify_event
const KNOWN_ATTRIBUTES = [
  { key: "finestra_aperta", label: "Finestra aperta", icon: "🪟", type: "bool", linkedEntityAttr: "finestra_entity_id" },
  { key: "porta_aperta", label: "Porta aperta", icon: "🚪", type: "bool", linkedEntityAttr: "porta_entity_id" },
  { key: "modalita_notturna_attiva", label: "Modalità notturna attiva", icon: "🌙", type: "bool" },
  { key: "target_effettivo", label: "Target effettivo", icon: "🎯", type: "number", unit: "°C" },
  { key: "accensione_notturna_automatica", label: "Acceso automaticamente di notte", icon: "🌙⚡", type: "bool" },
  { key: "accensione_notturna_abilitata", label: "Accensione notturna abilitata", icon: "🌙", type: "bool" },
  { key: "spegnimento_notturno_abilitato", label: "Spegnimento notturno abilitato", icon: "🌙", type: "bool" },
  { key: "spegnimento_fine_notte_abilitato", label: "Spegnimento fine notte abilitato", icon: "🌅", type: "bool" },
  { key: "spegnimento_fv_abilitato", label: "Spegnimento FV abilitato", icon: "☀️", type: "bool" },
  { key: "accensione_fv_abilitata", label: "Accensione FV abilitata", icon: "☀️", type: "bool" },
  { key: "termostato_abilitato", label: "Termostato abilitato (master)", icon: "🔌", type: "bool" },
  { key: "raffreddamento_rapido", label: "Raffreddamento rapido", icon: "❄️", type: "bool" },
  { key: "fascia_silenzio_attiva", label: "Fascia di silenzio attiva", icon: "🔇", type: "bool" },
  { key: "fv_surplus_buffer", label: "Buffer surplus FV", icon: "📊", type: "array" },
  { key: "dry_since", label: "DRY avviato alle", icon: "💧", type: "timestamp" },
  { key: "dry_end", label: "DRY termina alle", icon: "💧", type: "timestamp" },
  { key: "dry_elapsed_min", label: "Minuti DRY trascorsi", icon: "⏱️", type: "number", unit: "min" },
  { key: "spento_manualmente_da", label: "Spento manualmente da", icon: "✋", type: "timestamp" },
  { key: "blocco_riaccensione_attivo", label: "Blocco riaccensione attivo", icon: "🔒", type: "bool" },
  { key: "soglia_accensione_fv", label: "Soglia accensione", icon: "🌡️", type: "number", unit: "°C" },
  { key: "fv_basso_da", label: "FV insufficiente da", icon: "📉", type: "timestamp" },
  { key: "acceso_manualmente_da", label: "Acceso manualmente da (immunità FV)", icon: "✋", type: "timestamp" },
  { key: "sonda_esterna_bloccata", label: "Sonda esterna bloccata (fallback su interna)", icon: "📡", type: "bool" },
  { key: "modalita_esterna_non_gestita", label: "Modalità non gestita (caldo/ventilatore/auto)", icon: "⚠️", type: "bool" },
  { key: "ultimo_evento_notifica", label: "Ultimo evento notifica (storico espandibile)", icon: "🔔", type: "notify_event", dedicatedWidget: true },
  { key: "presenza_da", label: "Presenza rilevata da", icon: "🧍", type: "timestamp" },
  { key: "notte_sotto_target_da", label: "Sotto target notturno da", icon: "🌙", type: "timestamp" },
  { key: "snapshot_attivo", label: "Snapshot finestra attivo", icon: "📸", type: "bool" },
  { key: "climatizzatore_reale", label: "Entità climatizzatore reale", icon: "🔧", type: "text" },
  { key: "modalita_configurazione", label: "Modalità configurazione", icon: "⚙️", type: "mode_label" },
  { key: "fv_priorita", label: "Priorità FV (regolabile con frecce)", icon: "🔢", type: "number", dedicatedWidget: true },
  { key: "protezione_potenza_attiva", label: "Protezione potenza attiva", icon: "⚡", type: "bool" },
  { key: "protezione_potenza_da", label: "Protezione potenza da", icon: "⚡", type: "timestamp" },
  { key: "emergenza_caldo_attiva", label: "Emergenza caldo attiva", icon: "🔥", type: "bool" },
];

function findAttrDef(key) {
  return KNOWN_ATTRIBUTES.find((a) => a.key === key) || { key, label: key, icon: "•", type: "text" };
}

function formatTimestamp(value) {
  if (!value) return "—";
  const d = new Date(value);
  if (isNaN(d.getTime())) return String(value);
  const now = new Date();
  const sameDay = d.toDateString() === now.toDateString();
  const time = d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
  if (sameDay) return time;
  const date = d.toLocaleDateString("it-IT", { day: "2-digit", month: "2-digit" });
  return `${date} ${time}`;
}

function formatValue(def, value) {
  if (value === null || value === undefined || value === "") {
    if (def.type === "bool") return { text: "No", positive: false };
    return { text: "—", positive: null };
  }
  switch (def.type) {
    case "bool":
      return { text: value ? "Sì" : "No", positive: !!value };
    case "timestamp":
      return { text: formatTimestamp(value), positive: null };
    case "number": {
      const n = typeof value === "number" ? value : parseFloat(value);
      return { text: isNaN(n) ? String(value) : `${n}${def.unit ? " " + def.unit : ""}`, positive: null };
    }
    case "array": {
      if (!Array.isArray(value) || value.length === 0) return { text: "—", positive: null };
      return { text: value.map((v) => Math.round(v)).join(", "), positive: null };
    }
    case "notify_event": {
      if (typeof value === "object" && value.messaggio) {
        return { text: `${formatTimestamp(value.timestamp)} — ${value.messaggio}`, positive: null };
      }
      return { text: "—", positive: null };
    }
    case "mode_label": {
      const labels = { simple: "Semplificato", simple_fv: "Semplificato + FV", full: "Completo" };
      return { text: labels[value] || String(value), positive: null };
    }
    default:
      return { text: String(value), positive: null };
  }
}

class TermostatoDiagCard extends HTMLElement {
  setConfig(config) {
    if (!config.entity) {
      throw new Error("Devi specificare un'entità climate");
    }
    if (this._notifyHistoryExpanded === undefined) {
      this._notifyHistoryExpanded = false; // sopravvive ai re-render, si azzera solo su riconfigurazione
    }
    this._config = {
      title: "",
      color_by_state: true,
      display_style: "rows", // rows | badges
      show_attributes: [],
      ...config,
    };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  getCardSize() {
    return 2 + Math.ceil((this._config.show_attributes || []).length / 2);
  }

  _render() {
    if (!this._hass || !this._config) return;
    const stateObj = this._hass.states[this._config.entity];
    if (!stateObj) {
      this.innerHTML = `<ha-card><div style="padding:16px;color:var(--error-color);">Entità non trovata: ${this._config.entity}</div></ha-card>`;
      return;
    }

    // Se il dispositivo reale è in una modalità che questa integrazione
    // non gestisce (caldo, ventilazione, auto — impostata da fuori), lo
    // stato che riportiamo a Home Assistant resta "cool" per vincolo
    // tecnico, ma sarebbe fuorviante colorare la card e l'icona come se
    // stesse raffreddando. Usiamo un colore di avviso neutro dedicato.
    const unmanagedMode = !!stateObj.attributes.modalita_esterna_non_gestita;
    const stateKey = unmanagedMode ? "unmanaged" : (stateObj.state in STATE_COLORS ? stateObj.state : "unknown");
    const UNMANAGED_COLOR = { bg: "rgba(240, 180, 0, 0.15)", border: "#f0b400", shadow: "rgba(240, 180, 0, 0.2)" };
    const colors = this._config.color_by_state ? (unmanagedMode ? UNMANAGED_COLOR : (STATE_COLORS[stateKey] || DEFAULT_COLOR)) : null;
    const title = this._config.title || stateObj.attributes.friendly_name || this._config.entity;

    // Trasparenza dello sfondo, regolabile dalla configurazione della card
    // (0.1 = quasi trasparente, 1 = colore pieno) — si applica sia allo
    // sfondo colorato per stato che a quello neutro quando il clima è spento.
    const bgOpacity = this._config.background_opacity !== undefined ? this._config.background_opacity : 0.5;
    const cardStyle = colors
      ? `background-color:${applyOpacity(colors.bg, bgOpacity)};border:2px solid ${colors.border};box-shadow:0 2px 30px ${colors.shadow};border-radius:var(--ha-card-border-radius, 12px);padding:12px;`
      : `background-color:var(--card-background-color, #fff);border-radius:var(--ha-card-border-radius, 12px);padding:12px;`;

    const temp = stateObj.attributes.temperature;
    const curTemp = stateObj.attributes.current_temperature;
    const fanMode = stateObj.attributes.fan_mode;
    const fvPriorita = stateObj.attributes.fv_priorita;
    const isSimpleMode = ["semplificato", "semplificato_fv"].includes(stateObj.attributes.modalita_configurazione);
    const isSimpleFvMode = stateObj.attributes.modalita_configurazione === "semplificato_fv";

    // Temperatura "stanza" (sonda esterna, se configurata) e "clima" (sonda
    // interna del climatizzatore reale) mostrate separatamente — utile per
    // capire a colpo d'occhio se le due letture divergono molto, o durante
    // il fallback quando current_temperature mostra la sonda interna.
    const roomSensorEntity = stateObj.attributes.sonda_esterna_entity_id;
    const roomTempState = roomSensorEntity ? this._hass.states[roomSensorEntity] : null;
    const roomTemp = roomTempState && !isNaN(parseFloat(roomTempState.state)) ? parseFloat(roomTempState.state) : null;
    const realClimateEntity = stateObj.attributes.climatizzatore_reale;
    const realClimateState = realClimateEntity ? this._hass.states[realClimateEntity] : null;
    const climaTemp = realClimateState && realClimateState.attributes.current_temperature !== undefined
      ? realClimateState.attributes.current_temperature : null;

    // "ultimo_evento_notifica" e "fv_priorita" restano selezionabili come
    // prima, ma invece di una riga generica ora controllano la visibilità
    // dei rispettivi widget dedicati (storico espandibile, frecce +/-).
    const showAttrs = this._config.show_attributes || [];
    const showNotifyHistoryWidget = showAttrs.includes("ultimo_evento_notifica");
    const showPriorityWidget = showAttrs.includes("fv_priorita");
    const hideInactive = this._config.hide_inactive !== false; // default true
    let attrsHtml = "";
    if (showAttrs.length > 0) {
      // Tipi che hanno un concetto naturale di "attivo/presente" — se
      // hideInactive è true, li nascondiamo quando sono false/vuoti/null.
      // Numeri e testo semplice non hanno uno stato "inattivo", restano
      // sempre visibili.
      const hasActiveState = (type) => ["bool", "timestamp", "array", "notify_event"].includes(type);

      const visibleKeys = showAttrs.filter((key) => {
        const def = findAttrDef(key);
        if (def.dedicatedWidget) return false; // controlla solo il widget dedicato, niente riga generica
        const raw = stateObj.attributes[key];
        if (!hideInactive || !hasActiveState(def.type)) return true;
        if (def.type === "bool") return !!raw;
        if (def.type === "array") return Array.isArray(raw) && raw.length > 0;
        if (def.type === "notify_event") return !!(raw && raw.messaggio);
        return raw !== null && raw !== undefined && raw !== ""; // timestamp
      });

      const items = visibleKeys.map((key) => {
        const def = findAttrDef(key);
        const val = formatValue(def, stateObj.attributes[key]);
        const colorStyle =
          val.positive === true ? "color:#2e7d32;font-weight:600;" :
          val.positive === false ? "color:var(--secondary-text-color);" : "";
        // Se l'attributo è collegato a un'entità reale (es. porta/finestra
        // hanno il sensore configurato dietro), rendiamo l'elemento
        // cliccabile per aprire il dialog informazioni nativo di Home
        // Assistant su quel sensore specifico — utile per vedere lo
        // storico, l'ultimo aggiornamento, ecc. senza dover cercare
        // l'entità a parte.
        const linkedEntity = def.linkedEntityAttr ? stateObj.attributes[def.linkedEntityAttr] : null;
        const clickableAttr = linkedEntity ? ` data-more-info-entity="${linkedEntity}"` : "";
        if (this._config.display_style === "badges") {
          const bg = val.positive === true ? "rgba(46,125,50,0.15)" : "rgba(120,120,120,0.12)";
          // Booleano (mostrato solo se true, quindi l'icona basta da sola).
          // Per timestamp/eventi/array mostriamo anche il valore, che porta
          // un'informazione reale (orario, testo messaggio, numeri).
          const content = def.type === "bool"
            ? `<span title="${def.label}">${def.icon}</span>`
            : `<span title="${def.label}">${def.icon}</span><span>${val.text}</span>`;
          return `<span${clickableAttr} style="display:inline-flex;align-items:center;gap:4px;background:${bg};border-radius:12px;padding:4px 10px;margin:3px;font-size:12px;${colorStyle}${linkedEntity ? "cursor:pointer;" : ""}">
            ${content}
          </span>`;
        }
        return `<div${clickableAttr} style="display:flex;justify-content:space-between;padding:3px 0;font-size:13px;border-bottom:1px solid rgba(128,128,128,0.15);${linkedEntity ? "cursor:pointer;" : ""}">
          <span>${def.icon} ${def.label}</span><span style="${colorStyle}">${val.text}</span>
        </div>`;
      });
      const wrapper = this._config.display_style === "badges"
        ? `<div style="display:flex;flex-wrap:wrap;margin-top:10px;">${items.join("")}</div>`
        : `<div style="margin-top:10px;">${items.join("")}</div>`;
      attrsHtml = items.length > 0 ? wrapper : "";
    }

    // Storico eventi — sempre in fondo, a piena larghezza, con l'ultimo
    // evento sempre visibile e il resto espandibile con un tocco. Lo stato
    // di espansione è salvato sull'istanza (non nella config), quindi
    // sopravvive ai re-render continui della card senza richiudersi da solo.
    const notifyHistory = Array.isArray(stateObj.attributes.storico_notifiche) ? stateObj.attributes.storico_notifiche : [];
    let notifyHistoryHtml = "";
    if (notifyHistory.length > 0 && showNotifyHistoryWidget) {
      const latest = notifyHistory[0];
      const latestTime = latest.timestamp ? new Date(latest.timestamp).toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" }) : "";
      const olderRows = this._notifyHistoryExpanded
        ? notifyHistory.slice(1).map((ev) => {
            const t = ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" }) : "";
            return `<div style="font-size:11px;opacity:0.65;padding:3px 0;">${t} — ${ev.messaggio || ""}</div>`;
          }).join("")
        : "";
      notifyHistoryHtml = `
        <div style="border-top:0.5px solid rgba(128,128,128,0.25);padding-top:8px;margin-top:10px;">
          <button data-toggle-notify-history="1" style="width:100%;display:flex;justify-content:space-between;align-items:center;padding:8px 10px;background:rgba(0,0,0,0.04);border-radius:10px;border:none;text-align:left;cursor:pointer;">
            <span style="font-size:12px;opacity:0.8;">🔔 ultimo evento: ${latestTime} — ${latest.messaggio || ""}</span>
            <ha-icon icon="${this._notifyHistoryExpanded ? "mdi:chevron-up" : "mdi:chevron-down"}" style="--mdc-icon-size:14px;opacity:0.6;flex-shrink:0;margin-left:6px;"></ha-icon>
          </button>
          ${olderRows ? `<div style="padding:4px 10px;">${olderRows}</div>` : ""}
        </div>`;
    }

    // Pulsanti modalità: cool (blu), dry (giallo quando attivo), off (grigio).
    // Un tocco cambia subito la modalità reale del climatizzatore.
    // Se il dispositivo reale è in una modalità non gestita (caldo,
    // ventilazione, auto — impostata dal telecomando o da un'altra
    // automazione, mai da noi), NESSUNA delle 3 icone risulta "attiva":
    // lo stato riportato da questa entità è sempre "cool" per vincolo
    // tecnico anche in quel caso, ma sarebbe fuorviante mostrare
    // raffreddamento come attivo quando in realtà sta scaldando.
    const modeBtn = (mode, icon, label, activeBg, activeColor) => {
      const active = !unmanagedMode && stateObj.state === mode;
      const bg = active ? activeBg : "var(--card-background-color, #fff)";
      const color = active ? activeColor : "var(--secondary-text-color)";
      const border = active ? "none" : "1px solid var(--divider-color, #ccc)";
      return `<button data-mode="${mode}" aria-label="${label}" title="${label}"
        style="width:24px;height:24px;border-radius:50%;border:${border};background:${bg};color:${color};display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0;box-sizing:border-box;flex-shrink:0;">
        <ha-icon icon="${icon}" style="--mdc-icon-size:13px;"></ha-icon>
      </button>`;
    };
    const unmanagedBadge = unmanagedMode
      ? `<span title="Modalità non gestita da questa integrazione (caldo/ventilazione/auto impostata da fuori)"
          style="width:24px;height:24px;border-radius:50%;background:#f0b400;color:#4a3800;display:flex;align-items:center;justify-content:center;box-sizing:border-box;flex-shrink:0;">
          <ha-icon icon="mdi:alert" style="--mdc-icon-size:13px;"></ha-icon>
        </span>`
      : "";

    // Pulsante accensione/spegnimento: a differenza di cool/dry (colorati
    // solo quando sono la modalità attiva), questo resta SEMPRE colorato —
    // rosso quando il clima è spento, verde quando è acceso (in qualsiasi
    // modalità, gestita o no) — per essere riconoscibile a colpo d'occhio
    // senza dover distinguere le sfumature neutre di "non attivo".
    const isReallyOff = stateObj.state === "off";
    const powerBtn = `<button data-power-toggle="1" aria-label="${isReallyOff ? "Spento — tocca per accendere" : "Acceso — tocca per spegnere"}" title="${isReallyOff ? "Spento" : "Acceso"}"
      style="width:24px;height:24px;border-radius:50%;border:none;background:${isReallyOff ? "#d9302e" : "#2e9c4f"};color:#fff;display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0;box-sizing:border-box;flex-shrink:0;">
      <ha-icon icon="mdi:power" style="--mdc-icon-size:13px;"></ha-icon>
    </button>`;

    // Ventola: icona MDI che mostra già graficamente il livello (fan-speed-1/2/3).
    // Un tocco fa scorrere alla velocità successiva (bassa→media→alta→bassa).
    const fanIcons = { low: "mdi:fan-speed-1", medium: "mdi:fan-speed-2", high: "mdi:fan-speed-3" };
    // "auto" o altri valori non tra i 3 livelli fissi: mostriamo un'icona
    // ventola generica (in funzione, livello non specificato) — MAI
    // "fan-off" a meno che il clima sia realmente spento, altrimenti
    // sembrerebbe che il climatizzatore non stia facendo nulla quando in
    // realtà sta semplicemente regolando la ventola da solo.
    const fanIcon = fanIcons[fanMode] || (stateObj.state === "off" ? "mdi:fan-off" : "mdi:fan");
    const fanBtn = `<button data-fan-cycle="1" aria-label="Ventola ${fanMode || "—"}, tocca per cambiare" title="Ventola ${fanMode || "—"}"
      style="height:24px;border-radius:12px;border:1px solid var(--divider-color, #ccc);background:var(--card-background-color, #fff);display:flex;align-items:center;justify-content:center;gap:3px;padding:0 7px;box-sizing:border-box;cursor:pointer;margin-left:2px;flex-shrink:0;">
      <ha-icon icon="${fanIcon}" style="--mdc-icon-size:13px;"></ha-icon>
    </button>`;

    const modeButtonsHtml = `<div style="display:flex;align-items:center;gap:5px;height:24px;">
      ${unmanagedBadge}
      ${modeBtn("cool", "mdi:snowflake", "Raffreddamento", "#2e6fd9", "#fff")}
      ${modeBtn("dry", "mdi:water", "Deumidificatore", "#f0b400", "#4a3800")}
      ${powerBtn}
      ${fanBtn}
    </div>`;

    // Target con frecce — regola immediatamente (step di 1°), disponibile
    // solo nel modo Semplice/Semplice+FV (dove il target è sempre
    // ricalcolato da configurazione + eventuale regolazione da card).
    const tempDisplay = temp !== undefined ? (Math.round(temp * 10) / 10) + "°" : "—";
    const targetCellHtml = isSimpleMode ? `
      <div style="flex:1;text-align:center;padding:8px 4px;">
        <div style="font-size:10px;opacity:0.6;margin-bottom:2px;">target</div>
        <div style="display:flex;align-items:center;justify-content:center;gap:4px;">
          <button data-target-delta="-0.1" aria-label="Diminuisci target" title="Diminuisci target"
            style="width:16px;height:16px;border-radius:50%;border:1px solid var(--divider-color, #ccc);background:var(--card-background-color, #fff);display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0;box-sizing:border-box;flex-shrink:0;">
            <ha-icon icon="mdi:minus" style="--mdc-icon-size:10px;"></ha-icon>
          </button>
          <div style="font-size:18px;font-weight:700;line-height:1;min-width:40px;">${tempDisplay}</div>
          <button data-target-delta="0.1" aria-label="Aumenta target" title="Aumenta target"
            style="width:16px;height:16px;border-radius:50%;border:1px solid var(--divider-color, #ccc);background:var(--card-background-color, #fff);display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0;box-sizing:border-box;flex-shrink:0;">
            <ha-icon icon="mdi:plus" style="--mdc-icon-size:10px;"></ha-icon>
          </button>
        </div>
      </div>` : `
      <div style="flex:1;text-align:center;padding:8px 4px;">
        <div style="font-size:10px;opacity:0.6;margin-bottom:2px;">target</div>
        <div style="font-size:18px;font-weight:700;line-height:1;">${tempDisplay}</div>
      </div>`;


    // Priorità con frecce — regola immediatamente (step di 1), solo nel
    // modo Semplice+FV dove la priorità ha un effetto reale.
    const priorityControlHtml = (isSimpleFvMode && fvPriorita !== undefined && showPriorityWidget) ? `
      <div style="display:flex;align-items:center;justify-content:space-between;margin-top:12px;padding:6px 10px;background:rgba(0,0,0,0.04);border-radius:10px;">
        <span style="font-size:12px;opacity:0.75;display:flex;align-items:center;gap:5px;">
          <ha-icon icon="mdi:flag" style="--mdc-icon-size:14px;"></ha-icon>priorità FV
        </span>
        <div style="display:flex;align-items:center;gap:8px;">
          <button data-priority-delta="-1" aria-label="Diminuisci priorità" title="Diminuisci priorità"
            style="width:22px;height:22px;border-radius:50%;border:1px solid var(--divider-color, #ccc);background:var(--card-background-color, #fff);display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0;">
            <ha-icon icon="mdi:minus" style="--mdc-icon-size:12px;"></ha-icon>
          </button>
          <span style="font-size:13px;font-weight:700;min-width:16px;text-align:center;">${fvPriorita}</span>
          <button data-priority-delta="1" aria-label="Aumenta priorità" title="Aumenta priorità"
            style="width:22px;height:22px;border-radius:50%;border:1px solid var(--divider-color, #ccc);background:var(--card-background-color, #fff);display:flex;align-items:center;justify-content:center;cursor:pointer;padding:0;">
            <ha-icon icon="mdi:plus" style="--mdc-icon-size:12px;"></ha-icon>
          </button>
        </div>
      </div>` : "";

    this.innerHTML = `
      <ha-card style="overflow:hidden;background:transparent;--ha-card-background:transparent;">
        <div style="${cardStyle}">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div style="font-size:16px;font-weight:700;letter-spacing:0.5px;">${title}</div>
            ${modeButtonsHtml}
          </div>
          <div style="margin-top:14px;">
            <div style="display:flex;border:0.5px solid var(--divider-color, #ccc);border-radius:10px;overflow:hidden;">
              ${roomSensorEntity ? `
              <div style="flex:1;text-align:center;padding:8px 4px;border-right:0.5px solid var(--divider-color, #ccc);">
                <div style="font-size:10px;opacity:0.6;margin-bottom:2px;">stanza</div>
                <div style="font-size:18px;font-weight:700;line-height:1;">${roomTemp !== null ? (Math.round(roomTemp * 10) / 10) + "°" : "—"}</div>
              </div>` : ""}
              <div style="flex:1;text-align:center;padding:8px 4px;border-right:0.5px solid var(--divider-color, #ccc);">
                <div style="font-size:10px;opacity:0.6;margin-bottom:2px;">clima</div>
                <div style="font-size:18px;font-weight:700;line-height:1;">${climaTemp !== null ? (Math.round(climaTemp * 10) / 10) + "°" : "—"}</div>
              </div>
              ${targetCellHtml}
            </div>
          </div>
          ${priorityControlHtml}
          ${attrsHtml}
          ${notifyHistoryHtml}
        </div>
      </ha-card>
    `;

    this._attachControlListeners(stateObj);
  }

  _callService(domain, service, data) {
    if (this._hass && this._hass.callService) {
      this._hass.callService(domain, service, data);
    }
  }

  _attachControlListeners(stateObj) {
    const entityId = this._config.entity;

    this.querySelectorAll("[data-mode]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const mode = btn.getAttribute("data-mode");
        this._callService("climate", "set_hvac_mode", { entity_id: entityId, hvac_mode: mode });
      });
    });

    const powerToggleBtn = this.querySelector("[data-power-toggle]");
    if (powerToggleBtn) {
      powerToggleBtn.addEventListener("click", () => {
        // Vero toggle: se è spento accende (in raffreddamento, la modalità
        // di default), se è acceso (in qualunque modalità) spegne.
        const nextMode = stateObj.state === "off" ? "cool" : "off";
        this._callService("climate", "set_hvac_mode", { entity_id: entityId, hvac_mode: nextMode });
      });
    }

    const fanCycleBtn = this.querySelector("[data-fan-cycle]");
    if (fanCycleBtn) {
      fanCycleBtn.addEventListener("click", () => {
        const order = ["low", "medium", "high"];
        const current = stateObj.attributes.fan_mode;
        const idx = order.indexOf(current);
        const next = order[(idx + 1) % order.length] || "low";
        this._callService("climate", "set_fan_mode", { entity_id: entityId, fan_mode: next });
      });
    }

    this.querySelectorAll("[data-target-delta]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const delta = parseFloat(btn.getAttribute("data-target-delta"));
        this._callService("termostato_intelligente", "adjust_target", { entity_id: entityId, delta });
      });
    });

    this.querySelectorAll("[data-priority-delta]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const delta = parseFloat(btn.getAttribute("data-priority-delta"));
        this._callService("termostato_intelligente", "adjust_priority", { entity_id: entityId, delta });
      });
    });

    // Righe/badge con un'entità collegata (porta, finestra) — al click
    // apriamo il dialog informazioni nativo di Home Assistant su quella
    // entità specifica, usando l'evento standard che tutte le card native
    // e custom usano per questo scopo.
    this.querySelectorAll("[data-more-info-entity]").forEach((el) => {
      el.addEventListener("click", () => {
        const targetEntityId = el.getAttribute("data-more-info-entity");
        this.dispatchEvent(new CustomEvent("hass-more-info", {
          detail: { entityId: targetEntityId },
          bubbles: true,
          composed: true,
        }));
      });
    });

    const notifyToggleBtn = this.querySelector("[data-toggle-notify-history]");
    if (notifyToggleBtn) {
      notifyToggleBtn.addEventListener("click", () => {
        this._notifyHistoryExpanded = !this._notifyHistoryExpanded;
        this._render(); // re-render immediato, non aspetta il prossimo aggiornamento hass
      });
    }
  }

  static getConfigElement() {
    return document.createElement("termostato-diag-card-editor");
  }

  static getStubConfig(hass) {
    const climateEntities = Object.keys(hass.states).filter(
      (e) => e.startsWith("climate.") && hass.states[e].attributes.modalita_configurazione !== undefined
    );
    return {
      entity: climateEntities[0] || "",
      title: "",
      color_by_state: true,
      display_style: "rows",
      hide_inactive: true,
      show_attributes: ["modalita_notturna_attiva", "blocco_riaccensione_attivo", "finestra_aperta", "porta_aperta"],
    };
  }
}

// ============================================================================
// Editor grafico
// ============================================================================

class TermostatoDiagCardEditor extends HTMLElement {
  setConfig(config) {
    const firstTime = !this._config;
    this._config = { title: "", color_by_state: true, display_style: "rows", show_attributes: [], ...config };
    // Ridisegniamo solo al primissimo caricamento. Le chiamate successive a
    // setConfig arrivano dall'host di Home Assistant come "conferma" dopo
    // ogni nostro _emitConfig — se ridisegnassimo sempre, un campo di testo
    // come il titolo perderebbe il focus ad ogni singola lettera digitata
    // (l'intero DOM viene ricostruito da innerHTML). I controlli che
    // richiedono davvero un redraw (es. cambio entità, che cambia gli
    // attributi disponibili nei checkbox) lo chiamano già esplicitamente
    // nel proprio handler, subito sotto.
    if (firstTime) this._render();
  }

  set hass(hass) {
    const firstTime = !this._hass;
    this._hass = hass;
    // Ridisegna solo al primo arrivo di hass. Gli aggiornamenti successivi
    // (che in HA arrivano molte volte al secondo per ogni cambio di stato
    // in tutta la casa) NON devono ridisegnare l'editor, altrimenti ogni
    // tendina aperta si chiude e lo scroll si resetta a metà interazione.
    // I cambi espliciti (entità, checkbox, ecc.) chiamano già _render()
    // da soli nei rispettivi handler più sotto.
    if (firstTime) this._render();
  }

  _emitConfig() {
    this.dispatchEvent(new CustomEvent("config-changed", { detail: { config: this._config }, bubbles: true, composed: true }));
  }

  _render() {
    if (!this._hass) return;
    if (!this._config) return;

    const climateEntities = Object.keys(this._hass.states).filter(
      (e) => e.startsWith("climate.") && this._hass.states[e].attributes.modalita_configurazione !== undefined
    );
    const currentEntity = this._config.entity || "";

    // Attributi realmente presenti sull'entità selezionata (se ne esistono di
    // non elencati in KNOWN_ATTRIBUTES li mostriamo comunque, con etichetta grezza)
    let availableAttrs = KNOWN_ATTRIBUTES.map((a) => a.key);
    if (currentEntity && this._hass.states[currentEntity]) {
      const realAttrs = Object.keys(this._hass.states[currentEntity].attributes).filter(
        (k) => !["friendly_name", "hvac_modes", "min_temp", "max_temp", "fan_modes", "temperature", "current_temperature", "fan_mode", "supported_features", "hvac_action"].includes(k)
      );
      availableAttrs = Array.from(new Set([...availableAttrs.filter((k) => realAttrs.includes(k)), ...realAttrs]));
    }

    const entityOptions = climateEntities
      .map((e) => `<option value="${e}" ${e === currentEntity ? "selected" : ""}>${this._hass.states[e]?.attributes.friendly_name || e}</option>`)
      .join("");

    const checkboxes = availableAttrs
      .map((key) => {
        const def = findAttrDef(key);
        const checked = (this._config.show_attributes || []).includes(key);
        return `
          <label style="display:flex;align-items:center;gap:8px;padding:4px 0;font-size:14px;cursor:pointer;">
            <input type="checkbox" data-attr-key="${key}" ${checked ? "checked" : ""} />
            <span>${def.icon} ${def.label}</span>
          </label>`;
      })
      .join("");

    this.innerHTML = `
      <div style="padding:8px 0;">
        <div style="margin-bottom:14px;">
          <label style="display:block;font-size:13px;margin-bottom:4px;color:var(--secondary-text-color);">Entità climatizzatore</label>
          <select id="entity-select" style="width:100%;padding:8px;border-radius:6px;border:1px solid var(--divider-color,#ccc);background:var(--card-background-color,#fff);color:var(--primary-text-color);">
            <option value="">-- seleziona --</option>
            ${entityOptions}
          </select>
        </div>

        <div style="margin-bottom:14px;">
          <label style="display:block;font-size:13px;margin-bottom:4px;color:var(--secondary-text-color);">Titolo card (vuoto = usa nome entità)</label>
          <input id="title-input" type="text" value="${this._config.title || ""}" placeholder="es. SALA"
            style="width:100%;padding:8px;border-radius:6px;border:1px solid var(--divider-color,#ccc);background:var(--card-background-color,#fff);color:var(--primary-text-color);box-sizing:border-box;" />
        </div>

        <div style="margin-bottom:14px;">
          <label style="display:flex;align-items:center;gap:8px;font-size:14px;cursor:pointer;">
            <input id="color-toggle" type="checkbox" ${this._config.color_by_state ? "checked" : ""} />
            <span>Sfondo colorato in base allo stato (cool/dry/spento...)</span>
          </label>
        </div>

        <div style="margin-bottom:14px;">
          <label style="display:block;font-size:13px;margin-bottom:4px;color:var(--secondary-text-color);">
            Trasparenza sfondo (<span id="opacity-value">${Math.round((this._config.background_opacity !== undefined ? this._config.background_opacity : 0.5) * 100)}%</span>)
          </label>
          <input id="opacity-slider" type="range" min="0.1" max="1" step="0.05"
            value="${this._config.background_opacity !== undefined ? this._config.background_opacity : 0.5}"
            style="width:100%;" />
        </div>

        <div style="margin-bottom:14px;">
          <label style="display:block;font-size:13px;margin-bottom:6px;color:var(--secondary-text-color);">Stile visualizzazione attributi</label>
          <div style="display:flex;gap:16px;">
            <label style="display:flex;align-items:center;gap:6px;font-size:14px;cursor:pointer;">
              <input type="radio" name="display-style" value="rows" ${this._config.display_style !== "badges" ? "checked" : ""} />
              <span>Righe</span>
            </label>
            <label style="display:flex;align-items:center;gap:6px;font-size:14px;cursor:pointer;">
              <input type="radio" name="display-style" value="badges" ${this._config.display_style === "badges" ? "checked" : ""} />
              <span>Badge</span>
            </label>
          </div>
        </div>

        <div style="margin-bottom:14px;">
          <label style="display:flex;align-items:center;gap:8px;font-size:14px;cursor:pointer;">
            <input id="hide-inactive-toggle" type="checkbox" ${this._config.hide_inactive !== false ? "checked" : ""} />
            <span>Mostra solo attributi attivi/presenti (nascondi finestra chiusa, notte non attiva, DRY non in corso, ecc.)</span>
          </label>
        </div>

        <div>
          <label style="display:block;font-size:13px;margin-bottom:6px;color:var(--secondary-text-color);">Attributi da mostrare nella card</label>
          <div style="max-height:320px;overflow-y:auto;border:1px solid var(--divider-color,#ddd);border-radius:8px;padding:8px 12px;">
            ${checkboxes || '<div style="font-size:13px;opacity:0.7;">Seleziona prima un\'entità</div>'}
          </div>
        </div>
      </div>
    `;

    this.querySelector("#entity-select")?.addEventListener("change", (e) => {
      this._config = { ...this._config, entity: e.target.value };
      this._emitConfig();
      this._render();
    });

    this.querySelector("#title-input")?.addEventListener("input", (e) => {
      this._config = { ...this._config, title: e.target.value };
      this._emitConfig();
    });

    this.querySelector("#color-toggle")?.addEventListener("change", (e) => {
      this._config = { ...this._config, color_by_state: e.target.checked };
      this._emitConfig();
    });

    this.querySelector("#opacity-slider")?.addEventListener("input", (e) => {
      const value = parseFloat(e.target.value);
      this._config = { ...this._config, background_opacity: value };
      const label = this.querySelector("#opacity-value");
      if (label) label.textContent = `${Math.round(value * 100)}%`;
      this._emitConfig();
    });

    this.querySelector("#hide-inactive-toggle")?.addEventListener("change", (e) => {
      this._config = { ...this._config, hide_inactive: e.target.checked };
      this._emitConfig();
    });

    this.querySelectorAll('input[name="display-style"]').forEach((el) => {
      el.addEventListener("change", (e) => {
        if (e.target.checked) {
          this._config = { ...this._config, display_style: e.target.value };
          this._emitConfig();
        }
      });
    });

    this.querySelectorAll("input[data-attr-key]").forEach((el) => {
      el.addEventListener("change", (e) => {
        const key = e.target.getAttribute("data-attr-key");
        const current = new Set(this._config.show_attributes || []);
        if (e.target.checked) current.add(key);
        else current.delete(key);
        this._config = { ...this._config, show_attributes: Array.from(current) };
        this._emitConfig();
      });
    });
  }
}

customElements.define("termostato-diag-card", TermostatoDiagCard);
customElements.define("termostato-diag-card-editor", TermostatoDiagCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "termostato-diag-card",
  name: "Termostato Diag Card",
  description: "Card per Termostato Intelligente FV con sfondo colorato in base allo stato e attributi diagnostici configurabili da UI.",
  preview: true,
});
