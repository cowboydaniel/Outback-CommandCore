"""
DROIDCOM - Android Device Management Tool
Entry point for running the application standalone.
"""

import tkinter as tk
from .app import AndroidToolsModule


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
