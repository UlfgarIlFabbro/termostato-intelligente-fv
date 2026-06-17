# Termostato Intelligente FV

Integrazione custom per Home Assistant (HACS) che crea un'entità `climate`
"termostato intelligente" la quale pilota un climatizzatore reale in base a:

- **Finestra aperta** → blocco totale, avviso vocale, spegnimento ritardato e
  notifica, ripristino automatico alla chiusura.
- **Surplus fotovoltaico + batteria** → accensione automatica solo se c'è
  margine di produzione, SOC sufficiente e siamo nella fascia oraria attiva.
- **Temperatura** → regolazione a 3 livelli (caldo forte / sopra target / in
  range), con fan limitato a `low`/`medium`.
- **Presenza** → boost della ventola dopo N minuti di presenza continua.
- **Avvisi personalizzabili** → dispositivi Google (TTS) e notifiche
  Telegram/notify scelti e personalizzati dalla UI di configurazione, niente
  YAML.

Il repository è pubblicato su `https://github.com/UlfgarIlFabbro/termostato-intelligente-fv`.

Sostituisce le automazioni + l'helper `input_number` originali: il "target"
ora è semplicemente la temperatura impostata sull'entità climate creata da
questa integrazione.

## Installazione

1. Copia la cartella `custom_components/termostato_intelligente` nella
   cartella `custom_components` della tua configurazione Home Assistant
   (oppure pubblica questo repository su GitHub e aggiungilo come "custom
   repository" in HACS → Integrazioni → menu in alto a destra → Repository
   personalizzati).
2. Riavvia Home Assistant.
3. Vai su **Impostazioni → Dispositivi e servizi → Aggiungi integrazione** e
   cerca "Termostato Intelligente FV".
4. Compila i 4 step del form:
   - **Entità principali**: climatizzatore, sensore temperatura, finestra,
     presenza (opzionale).
   - **Fotovoltaico e batteria**: sensori FV/consumo/batteria e soglie
     (lascia vuoto per disattivare la logica FV).
   - **Soglie termiche**: scostamenti e tempistiche.
   - **Avvisi**: dispositivi Google su cui annunciare, messaggio vocale
     personalizzato, entità notify/Telegram a cui notificare, messaggio
     personalizzato.

Tutti i parametri (tranne le entità scelte al passo 1) sono modificabili in
qualsiasi momento da **Impostazioni → Dispositivi e servizi → Termostato
Intelligente FV → Opzioni**, senza dover ricreare l'integrazione.

## Prima di usarlo

- Il **delta di regolazione** (di quanto scostarsi dal target quando imposti
  la temperatura sul climatizzatore reale, default ±1°C) è configurabile
  nello step "Soglie termiche".
- Il **boost da presenza** ha un interruttore dedicato ("Attiva il boost da
  presenza") oltre ai minuti di conferma richiesti: se il tuo sensore di
  presenza dà falsi positivi puoi disattivarlo senza rimuovere il sensore
  selezionato, oppure aumentare i minuti di conferma per filtrare meglio i
  falsi allarmi.

## Note

- Il messaggio vocale e quello di notifica accettano variabili in stile
  Jinja: `{{ delay }}` (minuti di attesa), `{{ name }}` (nome del
  termostato), `{{ target }}` (temperatura target).
- Per Telegram l'integrazione usa preferibilmente le entità `notify.*`
  (il metodo moderno consigliato da Home Assistant); se non ne selezioni
  nessuna puoi indicare uno o più `chat_id` come fallback testuale.
