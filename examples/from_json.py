"""
Example usage of ASCIITerminalGUI library.
Demonstrates JSON-based menu creation.
"""


import sys
import time
from terminal_menu_lib import TerminalMenu


def example_from_json():
    """Example: Load menu from JSON file."""

    # Define callbacks
    def greet():
        print("\n👋 Hello from JSON menu!")
        input("\nPress Enter to continue...")

    def show_info():
        print("\n📋 This menu was loaded from JSON!")
        input("\nPress Enter to continue...")

    def setting_display():
        print("\n🖥️ Display settings would go here")
        input("\nPress Enter to continue...")

    def setting_audio():
        print("\n🔊 Audio settings would go here")
        input("\nPress Enter to continue...")

    def toggle_debug():
        print("\n🐛 Debug mode toggled")
        input("\nPress Enter to continue...")

    def reset_settings():
        print("\n♻️ Settings reset to defaults")
        input("\nPress Enter to continue...")

    def exit_app():
        print("\n👋 Goodbye!")
        time.sleep(1)
        sys.exit(0)

    # Action registry
    actions = {
        "greet": greet,
        "show_info": show_info,
        "setting_display": setting_display,
        "setting_audio": setting_audio,
        "toggle_debug": toggle_debug,
        "reset_settings": reset_settings,
        "exit_app": exit_app
    }

    # Load from JSON
    try:
        menu = TerminalMenu.from_json("menu_config.json", action_registry=actions)
        menu.run()
    except FileNotFoundError:
        print("❌ Error: menu_config.json not found!")
        print("Please create the configuration file first.")
        sys.exit(1)

if __name__ == '__main__':
    example_from_json()
