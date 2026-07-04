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

// Elenco completo attributi diagnostici conosciuti, con etichetta e icona.
// type serve a formattare il valore: bool | timestamp | number | text | array | notify_event
const KNOWN_ATTRIBUTES = [
  { key: "finestra_aperta", label: "Finestra aperta", icon: "🪟", type: "bool" },
  { key: "porta_aperta", label: "Porta aperta", icon: "🚪", type: "bool" },
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
  { key: "ultimo_evento_notifica", label: "Ultimo evento notifica", icon: "🔔", type: "notify_event" },
  { key: "presenza_da", label: "Presenza rilevata da", icon: "🧍", type: "timestamp" },
  { key: "notte_sotto_target_da", label: "Sotto target notturno da", icon: "🌙", type: "timestamp" },
  { key: "snapshot_attivo", label: "Snapshot finestra attivo", icon: "📸", type: "bool" },
  { key: "climatizzatore_reale", label: "Entità climatizzatore reale", icon: "🔧", type: "text" },
  { key: "modalita_configurazione", label: "Modalità configurazione", icon: "⚙️", type: "mode_label" },
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

    const stateKey = stateObj.state in STATE_COLORS ? stateObj.state : "unknown";
    const colors = this._config.color_by_state ? (STATE_COLORS[stateKey] || DEFAULT_COLOR) : null;
    const title = this._config.title || stateObj.attributes.friendly_name || this._config.entity;

    const cardStyle = colors
      ? `background-color:${colors.bg};border:2px solid ${colors.border};box-shadow:0 2px 30px ${colors.shadow};border-radius:18px;padding:12px;`
      : `border-radius:18px;padding:12px;`;

    const temp = stateObj.attributes.temperature;
    const curTemp = stateObj.attributes.current_temperature;
    const fanMode = stateObj.attributes.fan_mode;
    const hvacModeLabels = { cool: "Raffreddamento", dry: "Deumidificatore", off: "Spento", auto: "Auto", heat: "Riscaldamento", fan_only: "Ventola" };
    const hvacLabel = hvacModeLabels[stateObj.state] || stateObj.state;

    const showAttrs = this._config.show_attributes || [];
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
        if (this._config.display_style === "badges") {
          const bg = val.positive === true ? "rgba(46,125,50,0.15)" : "rgba(120,120,120,0.12)";
          // Booleano (mostrato solo se true, quindi l'icona basta da sola).
          // Per timestamp/eventi/array mostriamo anche il valore, che porta
          // un'informazione reale (orario, testo messaggio, numeri).
          const content = def.type === "bool"
            ? `<span title="${def.label}">${def.icon}</span>`
            : `<span title="${def.label}">${def.icon}</span><span>${val.text}</span>`;
          return `<span style="display:inline-flex;align-items:center;gap:4px;background:${bg};border-radius:12px;padding:4px 10px;margin:3px;font-size:12px;${colorStyle}">
            ${content}
          </span>`;
        }
        return `<div style="display:flex;justify-content:space-between;padding:3px 0;font-size:13px;border-bottom:1px solid rgba(128,128,128,0.15);">
          <span>${def.icon} ${def.label}</span><span style="${colorStyle}">${val.text}</span>
        </div>`;
      });
      const wrapper = this._config.display_style === "badges"
        ? `<div style="display:flex;flex-wrap:wrap;margin-top:10px;">${items.join("")}</div>`
        : `<div style="margin-top:10px;">${items.join("")}</div>`;
      attrsHtml = items.length > 0 ? wrapper : "";
    }

    this.innerHTML = `
      <ha-card>
        <div style="${cardStyle}">
          <div style="display:flex;justify-content:space-between;align-items:baseline;">
            <div style="font-size:16px;font-weight:700;letter-spacing:0.5px;">${title}</div>
            <div style="font-size:13px;opacity:0.85;">${hvacLabel}${fanMode ? " · " + fanMode : ""}</div>
          </div>
          <div style="display:flex;align-items:baseline;gap:10px;margin-top:6px;">
            <div style="font-size:34px;font-weight:700;">${curTemp !== undefined ? curTemp + "°" : "—"}</div>
            <div style="font-size:14px;opacity:0.85;">target ${temp !== undefined ? temp + "°" : "—"}</div>
          </div>
          ${attrsHtml}
        </div>
      </ha-card>
    `;
  }

  static getConfigElement() {
    return document.createElement("termostato-diag-card-editor");
  }

  static getStubConfig(hass) {
    const climateEntities = Object.keys(hass.states).filter((e) => e.startsWith("climate."));
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
    this._config = { title: "", color_by_state: true, display_style: "rows", show_attributes: [], ...config };
    this._render();
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

    const climateEntities = Object.keys(this._hass.states).filter((e) => e.startsWith("climate."));
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
