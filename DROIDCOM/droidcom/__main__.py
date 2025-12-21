import tkinter as tk

from .ui import AndroidToolsModule


def main():
    root = tk.Tk()
    root.title("Android Tools Module Test")
    root.geometry("700x800")
    root.option_add('*applicationVersion', '1.0.0')

    app = AndroidToolsModule(root)
    app.pack(expand=True, fill="both")

    root.mainloop()


if __name__ == "__main__":
    main()
