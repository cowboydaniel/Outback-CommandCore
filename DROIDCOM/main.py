"""
DROIDCOM - Android Device Management Tool
Entry point for running the application standalone.
"""

from pathlib import Path
import sys
import tkinter as tk

if __package__:
    from .app import AndroidToolsModule
else:
    module_root = Path(__file__).resolve().parent.parent
    sys.path.append(str(module_root))
    from DROIDCOM.app import AndroidToolsModule


def main():
    """Main entry point for the application"""
    root = tk.Tk()
    root.title("Android Tools Module Test")
    root.geometry("700x800")
    root.option_add('*applicationVersion', '1.0.0')

    app = AndroidToolsModule(root)
    app.pack(expand=True, fill="both")

    root.mainloop()


# For testing the module independently
if __name__ == "__main__":
    main()
