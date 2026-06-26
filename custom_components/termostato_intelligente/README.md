# 🌡️ Termostato Intelligente FV

**Termostato Intelligente FV** è una custom integration per Home Assistant che trasforma qualsiasi climatizzatore in un termostato smart, con gestione automatica basata su fotovoltaico, modalità notturna, deumidificazione intelligente e notifiche contestuali.

Sviluppata e mantenuta da [UlfgarIlFabbro](https://github.com/UlfgarIlFabbro).

---

## ✨ Caratteristiche principali

- **Tre modalità di configurazione**: Semplificato, Semplificato con Fotovoltaico, Completo
- **Gestione fotovoltaico**: accensione e spegnimento automatico basati su surplus energetico con sliding window anti-oscillazione
- **Controllo intelligente accensione manuale**: usa `sun.sun` per non intervenire sul clima acceso dall'utente dopo il tramonto
- **Modalità notturna**: target separato, accensione/spegnimento automatico, spegnimento a fine notte
- **Deumidificatore intelligente**: pre-trattamento in DRY prima del raffreddamento (modo semplificato)
- **Calibrazione sonda interna**: compensazione automatica della differenza tra sonda stanza e sonda interna del clima
- **Gestione finestra e porta**: avvisi e spegnimento automatico con ripristino
- **Notifiche contestuali**: Google Home (TTS) e Telegram con messaggi che spiegano il motivo di ogni azione
- **Fascia di silenzio**: silenzia gli avvisi negli orari configurati
- **Cascata multi-istanza**: gestione priorità tra più climatizzatori

---

## 📦 Installazione

### Tramite HACS (consigliato)
1. Apri HACS in Home Assistant
2. Vai su **Integrazioni** → menu in alto a destra → **Repository personalizzati**
3. Aggiungi `https://github.com/UlfgarIlFabbro/termostato-intelligente-fv` come tipo **Integrazione**
4. Cerca "Termostato Intelligente FV" e clicca **Installa**
5. Riavvia Home Assistant
6. Vai su **Impostazioni → Dispositivi e Servizi → Aggiungi integrazione** e cerca "Termostato Intelligente"

### Manuale
1. Scarica la cartella `custom_components/termostato_intelligente/` da questo repository
2. Copiala in `config/custom_components/termostato_intelligente/`
3. Riavvia Home Assistant
4. Aggiungi l'integrazione da **Impostazioni → Dispositivi e Servizi**

---

## 🚀 Modalità di configurazione

Al momento dell'aggiunta dell'integrazione ti viene chiesto di scegliere tra tre modalità. Puoi cambiarla in qualsiasi momento dalle opzioni dell'integrazione.

---

### 🟢 Modo Semplificato

La modalità più accessibile. Pochi campi, tutto il resto è automatico.

**Step 1 — Dispositivi**
- Climatizzatore da controllare (obbligatorio)
- Sensore temperatura stanza (opzionale — se non impostato usa la sonda interna del clima)
- Sensore finestra (opzionale)
- Sensore porta (opzionale)

**Step 2 — Temperature e orari**
- Temperatura target di giorno
- Temperatura target di notte + inizio/fine fascia notturna
- La fascia diurna viene ricavata automaticamente per differenza dalla notte
- Opzione spegnimento a fine modalità notturna (sempre o solo se acceso automaticamente)
- Opzione deumidificatore prima del raffreddamento

**Step 3 — Notifiche**
- Google Home e/o Telegram
- Checkbox individuali per ogni tipo di avviso
- Silenzia notifiche di notte (Google e Telegram separati)

#### Logica termica — con sonda esterna (valori decimali)

| Temperatura stanza | Azione |
|---|---|
| > target +2°C | Ventola **alta**, setpoint = sonda interna -2°C |
| > target +1.5°C | Ventola **media**, setpoint = sonda interna -2°C |
| > target +0.3°C | Ventola **bassa**, setpoint = sonda interna -1°C |
| ≤ target +0.3°C | Ventola **bassa**, setpoint = sonda interna (rallenta) |
| ≤ target -0.3°C per 15 min | **Spegni** |

Il clima si **accende** quando la stanza supera `target + 1.5°C`.

#### Logica termica — con sonda interna (valori interi)

Quando non è configurata una sonda esterna, il termostato usa la `current_temperature` riportata dal climatizzatore stesso. Poiché questa legge solo valori interi, le soglie si adattano:

| Temperatura stanza | Azione |
|---|---|
| > target +2°C | Ventola **alta**, setpoint = sonda interna -2°C |
| > target +1°C | Ventola **media**, setpoint = sonda interna -1°C |
| ≤ target +1°C | Ventola **bassa**, setpoint = sonda interna (rallenta) |
| ≤ target -1°C per 15 min | **Spegni** |

Il clima si **accende** quando la stanza supera `target + 2°C`.

#### Deumidificatore intelligente (opzionale)

Se abilitato, prima di avviare il raffreddamento il termostato tenta la deumidificazione:

**Con sonda esterna:**
- Stanza tra `target +0.3°C` e `target +1.5°C` → accende in **DRY** per max X minuti (configurabile, default 30)
- Se durante il DRY la stanza scende sotto `target -0.3°C` → spegne (ha funzionato!)
- Se sale sopra `target +1.5°C` o scadono i minuti → passa a **COOL**
- Già sopra `target +1.5°C` → **COOL diretto** senza passare dal DRY

**Con sonda interna:**
- Stanza tra `target +1°C` e `target +2°C` → accende in **DRY**
- Se scende sotto `target -1°C` → spegne
- Se sale sopra `target +2°C` o scadono i minuti → passa a **COOL**
- Già sopra `target +2°C` → **COOL diretto**

> 💡 **Perché è utile?** In climi umidi (come quello pugliese) la mattina presto la stanza può essere a 26°C con 70% di umidità. Il deumidificatore abbassa l'umidità percepita facendo sentire la stanza più fresca, consumando meno del raffreddamento pieno. Se in 30 minuti non basta, il termostato passa automaticamente al raffreddamento.

---

### 🔵 Modo Semplificato con Fotovoltaico

Identico al modo semplificato, con l'aggiunta di uno step per configurare l'uso del fotovoltaico.

**Step aggiuntivo — Fotovoltaico**
- Orario tramonto oggi (calcolato automaticamente, informativo)
- Orario limite controllo manuale (calcolato automaticamente, informativo)
- Ore di anticipo rispetto al tramonto (min 2h, default 2h)
- Sensore produzione FV (W)
- Sensore consumo rete (W)
- Sensore stato di carica batteria (%)
- Surplus minimo per accendere (W)
- SOC minimo batteria (%)
- Fascia oraria di accensione automatica
- Priorità e stagger tra più climatizzatori
- Spegnimento automatico con sliding window

#### Logica spegnimento intelligente — 4 casi

Il termostato distingue **chi ha acceso il clima** e agisce di conseguenza:

| Chi ha acceso | Spegnimento FV |
|---|---|
| Automazione FV | ✅ Spegne sempre quando FV insufficiente |
| Automazione notturna | ❌ Mai — solo spegnimento fine notte o target raggiunto |
| Utente manuale (prima di tramonto -2h) | ✅ Spegne se FV insufficiente |
| Utente manuale (dopo tramonto -2h) | ❌ Mai — l'utente gestisce manualmente |

> 💡 **Perché tramonto -2h?** Alle 17:40 (tramonto 19:40 - 2 ore) un impianto da 4kW produce già poco — probabilmente non abbastanza per giustificare il raffreddamento automatico. Dopo quell'ora l'automazione smette di intervenire sul clima acceso manualmente, lasciando libertà all'utente di usarlo per la serata. Il valore si adatta automaticamente alle stagioni grazie a `sun.sun` di Home Assistant.

#### Spegnimento per target raggiunto

Lo spegnimento per target raggiunto (stanza troppo fredda per 15 minuti) funziona **sempre**, indipendentemente da chi ha acceso il clima. Se la temperatura risale, il termostato verifica i criteri FV (surplus sufficiente, SOC batteria, fascia oraria) prima di riaccendere.

#### Sliding window per lo spegnimento FV

Il sistema campiona il surplus (`produzione - consumo`) ad ogni ciclo e mantiene un buffer degli ultimi N campioni. Lo spegnimento avviene **solo se tutti gli N campioni sono sotto la soglia configurata**. Un singolo picco di produzione non azzera il conteggio ma fa scorrere il buffer.

Esempio con 5 campioni e soglia 0W:
```
Buffer: [400, 450, 300, 600, 100] → max=600 > 0 → non spegne
Buffer: [450, 300, 600, 100, 300] → max=600 > 0 → non spegne
Buffer: [-50, -100, -200, -150, -80] → tutti < 0 → SPEGNE ✅
```

#### Cascata multi-istanza

Con più climatizzatori gestiti da istanze separate:
- **Priorità più bassa** (numero più piccolo) = si accende per **prima** e si spegne per **ultima**
- **Priorità più alta** (numero più grande) = si accende per **ultima** e si spegne per **prima**
- Lo **stagger** impone una pausa tra l'accensione/spegnimento di un clima e il successivo

---

### ⚙️ Modo Completo

Accesso completo a tutti i parametri dell'integrazione. Consigliato per utenti avanzati.

**Step 1 — Entità principali**
Climatizzatore, sensore temperatura, sensore finestra, sensore presenza, sensore porta.

**Step 2 — Fotovoltaico**
Configurazione completa FV con tutti i parametri di accensione e spegnimento.

**Step 3 — Profilo di regolazione**
- 🔵 **Bilanciato** — accende a +1.5°C, ventola alta da +2°C. Per uso quotidiano.
- 🔴 **Aggressivo** — accende a +1.2°C, ventola alta da +1.6°C. Per stanze grandi o molto esposte.
- 🟢 **Delicato** — accende a +1.8°C, ventola alta da +2.4°C. Silenzioso, per dormire.
- ⚙️ **Personalizzato** — imposta manualmente ogni soglia.

**Step 4 — Soglie termiche personalizzate** *(solo con profilo Personalizzato)*

**Step 5 — Modalità notturna**
- Fascia oraria notturna con target separato
- Accensione automatica notturna (senza FV)
- Spegnimento automatico per target raggiunto
- Spegnimento a fine modalità notturna (sempre / solo se acceso automaticamente)
- Calibrazione sonda interna, boost presenza, delay finestra, frequenza ciclo

**Step 6 — Notifiche e fascia di silenzio**
- Google Home (TTS) e Telegram configurabili separatamente
- Avvisi contestuali con motivo di ogni accensione/spegnimento
- Avviso dedicato per spegnimento fine notte
- Limite frequenza notifiche cambio setpoint
- Fascia di silenzio separata per Google e Telegram

#### Calibrazione sonda interna

Il climatizzatore ha una sonda interna che spesso legge temperature diverse dalla stanza reale. Il termostato calcola automaticamente la differenza e abbassa il setpoint per compensare, entro un massimo configurabile.

#### Fix transizioni sensori

Gli avvisi di apertura/chiusura porta e finestra scattano **solo su transizioni reali** (`off→on` e `on→off`). Le transizioni da/verso `unavailable` o `unknown` vengono ignorate, eliminando le notifiche spurie quando un sensore torna online.

---

## 🔔 Notifiche

### Modo semplificato
Checkbox individuali per ogni evento:
- Accensione / spegnimento automatico clima
- Finestra aperta / chiusa
- Porta aperta / chiusa
- Inizio / fine modalità notturna
- Silenziamento Google e Telegram separati durante la notte

### Modo completo
- Messaggi contestuali che spiegano il **motivo** di ogni accensione/spegnimento
- Template personalizzabili per ogni tipo di messaggio
- Limite di frequenza per notifiche cambio setpoint
- Fascia di silenzio configurabile separatamente per Google Home e Telegram
- Bypass automatico della fascia di silenzio per eventi critici

---

## 🔧 Switch ausiliari

Ogni istanza espone tre switch in Home Assistant:

| Switch | Funzione |
|---|---|
| **Master** | Abilita/disabilita completamente il termostato |
| **Accensione FV** | Abilita/disabilita solo l'accensione automatica da fotovoltaico |
| **Raffreddamento rapido** | Abbassa ulteriormente il setpoint e porta la ventola al massimo |

---

## 📊 Attributi esposti

| Attributo | Descrizione |
|---|---|
| `finestra_aperta` | Stato corrente finestra |
| `porta_aperta` | Stato corrente porta |
| `modalita_notturna_attiva` | Se siamo nella fascia notturna |
| `target_effettivo` | Target considerando l'offset notturno |
| `accensione_notturna_automatica` | Se il clima è stato acceso automaticamente di notte |
| `spegnimento_fv_abilitato` | Stato dello spegnimento FV |
| `fv_surplus_buffer` | Buffer corrente della sliding window (utile per debug) |
| `fascia_silenzio_attiva` | Se siamo nella fascia di silenzio |

---

## 🗂️ File dell'integrazione

```
custom_components/termostato_intelligente/
├── __init__.py
├── climate.py          # Logica principale del termostato
├── config_flow.py      # Configurazione guidata
├── const.py            # Costanti e valori di default
├── manifest.json       # Metadati integrazione
├── strings.json        # Stringhe UI (base inglese)
├── switch.py           # Switch ausiliari
├── util.py             # Funzioni di utilità
└── translations/
    ├── it.json         # Traduzione italiana
    └── en.json         # Traduzione inglese
```

---

## 📋 Versioni

| Versione | Note |
|---|---|
| v0.6.2 | Protezione potenza: spegnimento automatico per evitare distacco contatore, riaccensione automatica, cascata multi-clima |
| v0.6.1 | Fix SIMPLE_NIGHT_END_LIMBO_H mancante in const.py |
| v0.6.0 | Riscrittura logica termica semplificata: DRY sempre all accensione, soglia configurabile, 1h limbo post-notte, riaccensione FV automatica dopo calo |
| v0.5.5 | Notifiche Google Home e Telegram separate per ogni evento nel modo semplificato, aggiunta notifica cambio temperatura, fix timer DRY dopo riavvio HA |
| v0.5.4 | Notifiche Google Home e Telegram separate per ogni evento nel modo semplificato, aggiunta notifica cambio temperatura |
| v0.5.4 | Rimozione campi orario fascia FV nel modo semplificato — finestra calcolata automaticamente da fine notte a tramonto -2h |
| v0.5.3 | Fix entità non visibili nella pagina integrazione (DeviceInfo), fix cambio modalità dalle opzioni, fix ImportError DAY_END/START |
| v0.5.2 | Fix ImportError DEFAULT_SIMPLE_DAY_END |
| v0.5.1 | Fix e aggiornamenti modo semplificato FV |
| v0.5.0 | Tre modalità di configurazione, modo semplificato con deumidificatore intelligente, controllo tramonto con `sun.sun`, logica spegnimento 4 casi, rimozione orari giorno |
| v0.4.1 | Limite frequenza notifiche cambio setpoint |
| v0.4.0 | Sliding window FV, fix sensori porta/finestra, spegnimento fine notte |
| v0.3.3 | Prima versione stabile pubblica |

---

## 📄 Licenza

MIT License — libero utilizzo, modifica e distribuzione con attribuzione.
