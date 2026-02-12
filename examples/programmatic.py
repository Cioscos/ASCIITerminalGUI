"""
Example usage of ASCIITerminalGUI library.
Demonstrates programmatic menu creation.
"""

import sys
import time
from terminal_menu_lib import TerminalMenu, Entry


def example_programmatic():
    """Example: Build menu programmatically."""

    def greet():
        print("\n✨ Ciao! Benvenuto in ASCIITerminalGUI!")
        input("\nPremi Enter per continuare...")

    def show_info():
        print("\n📚 ASCIITerminalGUI - Libreria TUI Python")
        print("Versione: 1.0.0")
        print("Caratteristiche:")
        print("  • Navigazione con frecce")
        print("  • Supporto multi-pagina")
        print("  • Cross-platform (Windows/Linux)")
        print("  • Configurazione JSON")
        print("  • Ridimensionamento automatico")
        input("\nPremi Enter per continuare...")

    def calculator():
        print("\n🔢 Calcolatrice Semplice")
        try:
            a = float(input("Primo numero: "))
            b = float(input("Secondo numero: "))
            print(f"\nRisultato: {a} + {b} = {a + b}")
        except ValueError:
            print("❌ Input non valido!")
        input("\nPremi Enter per continuare...")

    def exit_app():
        print("\n👋 Arrivederci!")
        time.sleep(1)
        sys.exit(0)

    # Create menu
    menu = TerminalMenu()

    # Home page
    home = menu.add_page("home", "🏠 Menu Principale")
    home.add_entry(Entry("Saluta", action=greet))
    home.add_entry(Entry("Informazioni", action=show_info))
    home.add_entry(Entry("Calcolatrice", action=calculator))
    home.add_entry(Entry("Vai a Strumenti", next_page="tools"))
    home.add_entry(Entry("Esci", action=exit_app))

    # Tools page
    tools = menu.add_page("tools", "🔧 Strumenti")
    tools.add_entry(Entry("Strumento 1", action=lambda: print("\nStrumento 1")))
    tools.add_entry(Entry("Strumento 2", action=lambda: print("\nStrumento 2")))
    tools.add_entry(Entry("Impostazioni", next_page="settings"))
    tools.add_entry(Entry("Torna a Home", next_page="home"))

    # Settings page
    settings = menu.add_page("settings", "⚙️ Impostazioni")
    settings.add_entry(Entry("Display", action=lambda: print("\nImpostazioni Display")))
    settings.add_entry(Entry("Audio", action=lambda: print("\nImpostazioni Audio")))
    settings.add_entry(Entry("Torna Indietro", next_page="tools"))

    menu.set_start_page("home")
    menu.run()

if __name__ == '__main__':
    example_programmatic()
