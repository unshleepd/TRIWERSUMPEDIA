import tkinter as tk
from gui import TriwersumGame

def main():
    """
    Main entry point for the Triwersum Roguelike game.
    Initializes the Tkinter window and starts the game loop.
    """
    try:
        root = tk.Tk()
        game = TriwersumGame(root)
        root.mainloop()
    except tk.TclError:
        print("Could not open display. This is expected in a headless environment.")
        print("To run the game, please use a desktop environment with a display server.")

if __name__ == "__main__":
    main()
