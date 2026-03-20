import customtkinter as ctk
from ui import App

def main():
    root = ctk.CTk()
    try:
        root.iconbitmap("icon.ico")
    except Exception:
        pass

    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
