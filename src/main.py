import tkinter as tk
from gui import GameGUI
from game_logic import GameLogic
import traceback

def main():
    """
    Main entry point for the Triwersum Roguelike game.
    """
    try:
        root = tk.Tk()
        # First, create the logic core of the game
        game_logic = GameLogic()
        # Then, create the GUI, passing the logic to it
        app = GameGUI(root, game_logic)
        root.mainloop()
    except tk.TclError as e:
        print("Could not open display. This is expected in a headless environment.")
        print("--- Running non-GUI verification ---")
        try:
            print("Initializing GameLogic...")
            game_logic_check = GameLogic()
            assert game_logic_check.player is not None, "Player should be initialized."
            assert game_logic_check.map is not None, "Map should be initialized."
            assert len(game_logic_check.map.tiles) > 0, "Map tiles should be generated."
            assert len(game_logic_check.map.entities) > 1, "Map should have player and other entities."
            print("GameLogic initialization... PASSED.")

            print("\nTesting Save/Load cycle...")
            save_path = 'verification_save.json'
            game_logic_check.save_game(save_path)

            new_logic = GameLogic()
            load_success = new_logic.load_game(save_path)

            assert load_success, "Game should load successfully."
            assert new_logic.player.level == game_logic_check.player.level, "Player level should match after load."
            assert new_logic.map.width == game_logic_check.map.width, "Map width should match after load."
            print("Save/Load cycle... PASSED.")
            print("\n--- Non-GUI verification finished successfully! ---")

        except Exception as check_e:
            print("\n--- Non-GUI verification FAILED! ---")
            print(f"An error occurred during the check: {check_e}")
            traceback.print_exc()

if __name__ == "__main__":
    main()
