# ASCIITerminalGUI

A complete, self-contained Python library for building interactive terminal menus with keyboard navigation, multi-page support, and beautiful ASCII/Unicode rendering.

> 🇮🇹 **Versione Italiana**: [Leggi la documentazione in italiano](docs/README_it.md)

## 🚀 Features

- ✅ **Cross-platform**: Works seamlessly on Windows, Linux, and macOS
- ✅ **Intuitive Navigation**: Arrow keys (up/down), Enter to select, Esc to go back
- ✅ **Multi-page Support**: Create interconnected menu pages with navigation
- ✅ **Flexible Configuration**: Load from JSON or build programmatically
- ✅ **Responsive Design**: Automatically adapts to terminal resizing
- ✅ **ANSI Colors**: Colorful interface with selection highlighting
- ✅ **Zero External Dependencies**: Uses only Python standard library
- ✅ **Type Hints**: Fully annotated for better IDE support and code completion

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/asciiterminalgui.git
cd asciiterminalgui

# Install in development mode
pip install -e .
```


## 🎯 Quick Start

### Programmatic Example

```python
from terminal_menu_lib import TerminalMenu, Entry

def hello():
    print("\nHello World!")
    input("\nPress Enter to continue...")

def exit_app():
    import sys
    sys.exit(0)

# Create menu
menu = TerminalMenu()

# Create home page
home = menu.add_page("home", "Main Menu")
home.add_entry(Entry("Say Hello", action=hello))
home.add_entry(Entry("Go to Settings", next_page="settings"))
home.add_entry(Entry("Exit", action=exit_app))

# Create settings page
settings = menu.add_page("settings", "Settings")
settings.add_entry(Entry("Option 1", action=lambda: print("\nOption 1 selected")))
settings.add_entry(Entry("Option 2", action=lambda: print("\nOption 2 selected")))
settings.add_entry(Entry("Back to Home", next_page="home"))

# Run menu
menu.set_start_page("home")
menu.run()
```


### JSON Configuration Example

**menu_config.json**:

```json
{
  "pages": {
    "home": {
      "title": "Main Menu",
      "entries": [
        {"label": "Option 1", "action": "greet", "next_page": null},
        {"label": "Go to Settings", "action": null, "next_page": "settings"},
        {"label": "Exit", "action": "exit_app", "next_page": null}
      ]
    },
    "settings": {
      "title": "Settings",
      "entries": [
        {"label": "Display Settings", "action": "setting_display", "next_page": null},
        {"label": "Back to Home", "action": null, "next_page": "home"}
      ]
    }
  },
  "start_page": "home"
}
```

**Python code**:

```python
from terminal_menu_lib import TerminalMenu

# Define callbacks
def greet():
    print("\nHello from JSON menu!")
    input("\nPress Enter to continue...")

def setting_display():
    print("\nDisplay settings...")
    input("\nPress Enter to continue...")

def exit_app():
    import sys
    sys.exit(0)

# Action registry
actions = {
    "greet": greet,
    "setting_display": setting_display,
    "exit_app": exit_app
}

# Load and run
menu = TerminalMenu.from_json("menu_config.json", action_registry=actions)
menu.run()
```


## 🎨 Customization

You can customize colors and appearance:

```python
from terminal_menu_lib import TerminalMenu, Colors

menu = TerminalMenu(
    theme_color=Colors.BRIGHT_MAGENTA,      # Border and title color
    selected_bg=Colors.BG_BRIGHT_MAGENTA,   # Selected item background
    selected_fg=Colors.WHITE,               # Selected item text color
    min_width=50,                           # Minimum menu width
    min_height=15                           # Minimum menu height
)
```

## 📋 JSON Configuration Format

```json
{
  "pages": {
    "page_identifier": {
      "title": "Page Display Title",
      "entries": [
        {
          "label": "Entry Label Text",
          "action": "function_name_in_registry",
          "next_page": "target_page_identifier"
        }
      ]
    }
  },
  "start_page": "initial_page_identifier"
}
```


## 🧪 Running Examples

```bash
# Run built-in example
python terminal_menu_lib.py

# Run advanced examples
cd examples
python example_usage.py
```


## 🐛 Troubleshooting

### Arrow keys not working on Windows

Make sure your terminal supports ANSI escape codes. Use Windows Terminal or enable VT100 emulation.

### Arrow keys not working on Linux

Ensure your terminal is properly configured. The library uses standard escape sequences (`ESC[A/B/C/D`).

### Menu doesn't resize properly

The library checks terminal size periodically. If issues persist, try restarting the menu application.

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📚 Additional Documentation

- [Italian Documentation](docs/README_it.md) - Documentazione completa in italiano
- [Examples](examples) - More usage examples


## 🔗 Links

- **Repository**: https://github.com/Cioscos/ASCIITerminalGUI
- **Issues**: https://github.com/Cioscos/ASCIITerminalGUI/issues


## ⭐ Star History

If you find this library useful, please consider giving it a star on GitHub!

---

Made with ❤️ by the Cioscos
