# Termostato Intelligente FV — Istruzioni

Guida rapida a configurazione e logica di funzionamento, aggiornata alla v0.1.3.

## Aggiornamento

1. HACS → Termostato Intelligente FV → Aggiorna.
2. Riavvia Home Assistant.
3. Per ciascun termostato: Impostazioni → Dispositivi e servizi → Termostato Intelligente FV → Configura, e rivedi i nuovi campi descritti sotto.

## I 3 interruttori ausiliari

Ogni termostato crea automaticamente 3 entità switch:

- **Abilita Termostato Intelligente** (default ON) — interruttore master. Se spento, il termostato non fa assolutamente nulla (né regolazione né accensione da FV).
- **Accensione automatica da FV** (default ON) — se acceso, nella fascia oraria configurata il sistema accende il climatizzatore quando c'è surplus fotovoltaico sufficiente.
- **Raffreddamento rapido** (default OFF) — se acceso, spinge più forte nelle 3 fasce calde (vedi sotto).

La regolazione termica (le 5 fasce) gira **sempre**, indipendentemente da questi switch, tranne quando il master è spento.

## Le 5 fasce termiche

Calcolate confrontando la temperatura della stanza con il target (più eventuale scostamento notturno, vedi sotto):

| Fascia | Condizione | Setpoint inviato al clima | Ventola |
|---|---|---|---|
| Caldo estremo | stanza > target + soglia estrema | target − scostamento estremo | alta |
| Caldo forte | stanza > target + soglia forte | target − scostamento | media |
| Caldo | stanza > target + soglia caldo | target − scostamento | bassa |
| Vicino al target | stanza > target − margine | target | bassa |
| Sotto target | altrimenti | target + scostamento | bassa |

Tutte le soglie e gli scostamenti sono configurabili nello step "Soglie termiche e tempistiche".

## Raffreddamento rapido

Quando l'interruttore è acceso, nelle 3 fasce calde (estremo/forte/caldo — non nelle altre due) il sistema forza la ventola al massimo e abbassa il setpoint di un ulteriore grado rispetto al normale.

## Calibrazione automatica sonda interna del climatizzatore (NOVITÀ)

**Il problema che risolve:** molti climatizzatori hanno una propria sonda di temperatura interna, spesso diversa (di solito più "fresca") da quella reale della stanza. Se il termostato intelligente manda al clima un setpoint di 25°C mentre la sua sonda interna legge già 24°C, il climatizzatore si considera "soddisfatto" e smette di raffreddare, anche se in realtà la stanza è più calda del target.

**Come funziona la correzione:** ad ogni ciclo di controllo (ogni "Ogni quanto ricontrollare", default 5 minuti), il sistema legge anche la temperatura interna riportata dal climatizzatore stesso. Se questa è inferiore a quella della sonda ambiente, la differenza viene sottratta dal setpoint che viene inviato al climatizzatore, fino a un massimo configurabile (campo "Scostamento massimo calibrazione sonda interna", default 3°C, per sicurezza). In questo modo il compressore continua a lavorare finché la sua sonda interna non scende al livello realmente corrispondente al target in stanza.

Se il climatizzatore non espone la propria temperatura interna, questa correzione non si applica e il comportamento resta quello originale.

Non richiede nessuna configurazione aggiuntiva oltre al limite massimo (già impostato con un default sensato).

## Modalità notturna (NOVITÀ)

Tre nuovi campi nello step "Soglie termiche e tempistiche":

- **Inizio modalità notturna** (es. 23:00)
- **Fine modalità notturna** (es. 07:00 — gestisce correttamente l'attraversamento della mezzanotte)
- **Scostamento target notturno** in gradi, es. +1°C (default 0°C = modalità disattivata)

Durante la fascia oraria configurata, la regolazione interna usa target+scostamento invece del target puro. **Il target che vedi e imposti tu nel pannello del termostato non cambia mai** — resta sempre quello scelto da te; è solo il calcolo interno (quale temperatura mandare realmente al condizionatore) che tiene conto dello scostamento notturno.

Per disattivare la modalità notturna basta lasciare lo scostamento a 0°C.

## Priorità e distacco accensione da FV

Per evitare che tutti i climatizzatori si accendano insieme quando c'è molta produzione solare (con conseguente picco di consumo che la produzione FV non riesce a coprire istantaneamente):

- **Priorità di accensione** (1-99, default 50, più basso = priorità più alta): tra più termostati pronti ad accendersi nello stesso momento, parte solo quello con priorità migliore.
- **Distacco minimo tra le accensioni FV** (minuti, default 5): tempo minimo che deve passare tra l'accensione di un climatizzatore (da parte di qualsiasi termostato di questa integrazione) e la successiva. Ad ogni controllo successivo, il sistema verifica di nuovo se il surplus FV è ancora sufficiente prima di accendere il termostato successivo in coda.

## Bypass automatico sensori mancanti

Se il sensore finestra o il sensore presenza non sono configurati (o sono temporaneamente non disponibili/unavailable in Home Assistant), la relativa funzione viene semplicemente bypassata senza bloccare il resto della regolazione:
- Finestra non disponibile → considerata sempre chiusa.
- Presenza non disponibile → nessun boost da presenza, ma il resto funziona normalmente.

## Attributi extra dell'entità climate

Per debug/trasparenza, l'entità climate espone anche:
- `finestra_aperta`, `snapshot_attivo`, `presenza_da`, `climatizzatore_reale`
- `termostato_abilitato`, `accensione_fv_abilitata`, `raffreddamento_rapido`
- `modalita_notturna_attiva`, `target_effettivo` (il target realmente usato in quel momento, comprensivo di eventuale scostamento notturno)

## Card Lovelace consigliata

Vedi il messaggio precedente nella chat con lo YAML pronto per una card a griglia con i 4 termostati e i relativi interruttori.
