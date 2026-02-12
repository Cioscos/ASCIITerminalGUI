# ASCIITerminalGUI

Una libreria Python completa e indipendente per la creazione di menu interattivi da terminale con navigazione da tastiera, supporto multi-pagina e rendering ASCII/Unicode accattivante.

> 🇬🇧 **English Version**: [Read the documentation in English](../README.md)

## 🚀 Funzionalità

- ✅ **Cross-platform**: Funziona perfettamente su Windows, Linux e macOS
- ✅ **Navigazione Intuitiva**: Tasti freccia (su/giù), Invio per selezionare, Esc per tornare indietro
- ✅ **Supporto Multi-pagina**: Crea pagine di menu interconnesse con navigazione fluida
- ✅ **Configurazione Flessibile**: Caricamento da JSON o creazione programmatica
- ✅ **Design Reattivo**: Si adatta automaticamente al ridimensionamento del terminale
- ✅ **Colori ANSI**: Interfaccia colorata con evidenziazione della selezione
- ✅ **Zero Dipendenze Esterne**: Utilizza solo la libreria standard di Python
- ✅ **Type Hints**: Completamente annotato per un migliore supporto IDE e completamento del codice

## 📦 Installazione

```bash
# Clona il repository
git clone [https://github.com/tuousername/asciiterminalgui.git](https://github.com/tuousername/asciiterminalgui.git)
cd asciiterminalgui

# Installa in modalità sviluppo
pip install -e .
```


## 🎯 Avvio Rapido

### Esempio Programmatico

```python
from terminal_menu_lib import TerminalMenu, Entry

def hello():
    print("\nCiao Mondo!")
    input("\nPremi Invio per continuare...")

def exit_app():
    import sys
    sys.exit(0)

# Crea il menu
menu = TerminalMenu()

# Crea la pagina principale
home = menu.add_page("home", "Menu Principale")
home.add_entry(Entry("Dì Ciao", action=hello))
home.add_entry(Entry("Vai a Impostazioni", next_page="settings"))
home.add_entry(Entry("Esci", action=exit_app))

# Crea la pagina impostazioni
settings = menu.add_page("settings", "Impostazioni")
settings.add_entry(Entry("Opzione 1", action=lambda: print("\nOpzione 1 selezionata")))
settings.add_entry(Entry("Opzione 2", action=lambda: print("\nOpzione 2 selezionata")))
settings.add_entry(Entry("Torna alla Home", next_page="home"))

# Avvia il menu
menu.set_start_page("home")
menu.run()
```


### Esempio Configurazione JSON

**menu_config.json**:

```json
{
  "pages": {
    "home": {
      "title": "Menu Principale",
      "entries": [
        {"label": "Opzione 1", "action": "greet", "next_page": null},
        {"label": "Vai a Impostazioni", "action": null, "next_page": "settings"},
        {"label": "Esci", "action": "exit_app", "next_page": null}
      ]
    },
    "settings": {
      "title": "Impostazioni",
      "entries": [
        {"label": "Impostazioni Display", "action": "setting_display", "next_page": null},
        {"label": "Torna alla Home", "action": null, "next_page": "home"}
      ]
    }
  },
  "start_page": "home"
}
```

**Codice Python**:

```python
from terminal_menu_lib import TerminalMenu

# Definisci i callback
def greet():
    print("\nCiao dal menu JSON!")
    input("\nPremi Invio per continuare...")

def setting_display():
    print("\nImpostazioni display...")
    input("\nPremi Invio per continuare...")

def exit_app():
    import sys
    sys.exit(0)

# Registro delle azioni
actions = {
    "greet": greet,
    "setting_display": setting_display,
    "exit_app": exit_app
}

# Carica e avvia
menu = TerminalMenu.from_json("menu_config.json", action_registry=actions)
menu.run()
```


## 🎨 Personalizzazione

Puoi personalizzare colori e aspetto:

```python
from terminal_menu_lib import TerminalMenu, Colors

menu = TerminalMenu(
    theme_color=Colors.BRIGHT_MAGENTA,      # Colore bordo e titolo
    selected_bg=Colors.BG_BRIGHT_MAGENTA,   # Sfondo dell'elemento selezionato
    selected_fg=Colors.WHITE,               # Colore testo dell'elemento selezionato
    min_width=50,                           # Larghezza minima del menu
    min_height=15                           # Altezza minima del menu
)
```


## 📋 Formato Configurazione JSON

```json
{
  "pages": {
    "identificatore_pagina": {
      "title": "Titolo Visualizzato Pagina",
      "entries": [
        {
          "label": "Testo Etichetta Voce",
          "action": "nome_funzione_nel_registro",
          "next_page": "identificatore_pagina_destinazione"
        }
      ]
    }
  },
  "start_page": "identificatore_pagina_iniziale"
}
```


## 🧪 Eseguire gli Esempi

```bash
# Esegui l'esempio integrato
python terminal_menu_lib.py

# Esegui gli esempi avanzati
cd examples
python example_usage.py
```


## 🐛 Risoluzione dei Problemi

### I tasti freccia non funzionano su Windows

Assicurati che il tuo terminale supporti i codici di escape ANSI. Usa Windows Terminal o abilita l'emulazione VT100.

### I tasti freccia non funzionano su Linux

Assicurati che il terminale sia configurato correttamente. La libreria utilizza sequenze di escape standard (`ESC[A/B/C/D`).

### Il menu non si ridimensiona correttamente

La libreria controlla periodicamente la dimensione del terminale. Se i problemi persistono, prova a riavviare l'applicazione del menu.

## 📄 Licenza

Licenza MIT - Vedere il file LICENSE per i dettagli

## 🤝 Contribuire

I contributi sono benvenuti! Sentiti libero di inviare una Pull Request.

## 📚 Documentazione Aggiuntiva

- [English Documentation](../README.md) - Full documentation in English
- [Examples](../examples) - Ulteriori esempi di utilizzo


## 🔗 Link

- **Repository**: https://github.com/Cioscos/ASCIITerminalGUI
- **Issues**: https://github.com/Cioscos/ASCIITerminalGUI/issues


## ⭐ Star History

Se trovi utile questa libreria, considera di lasciarci una stella su GitHub!

***

Fatto con ❤️ da Cioscos
