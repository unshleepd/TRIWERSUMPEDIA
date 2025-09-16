import tkinter as tk
from tkinter import font as tkfont, messagebox
from functools import partial
from game_logic import GameLogic
from data_classes import NPC, Enemy

class Tooltip:
    # ... full implementation unchanged ...
    pass

class TriwersumGame:
    def __init__(self, root):
        self.root = root; self.root.title("Triwersum Roguelike"); self.root.configure(bg="#1a1a1a")
        self.bold_font = tkfont.Font(family="Helvetica", size=10, weight="bold")
        self.map_font = tkfont.Font(family="Courier", size=20, weight="bold")
        self.grid_width, self.grid_height, self.cell_size = 15, 12, 40
        self.game_logic = GameLogic(self.grid_width, self.grid_height)
        self.player_text_id, self.entity_text_ids = None, {}
        main_frame = tk.Frame(root, bg="#1a1a1a"); main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(main_frame, width=self.grid_width*self.cell_size, height=self.grid_height*self.cell_size, bg="#222", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=(0, 10)); self.canvas.bind("<Button-1>", self.handle_map_click)
        sidebar = tk.Frame(main_frame, bg="#1a1a1a"); sidebar.pack(side=tk.RIGHT, fill=tk.Y, expand=True)
        self.stats_labels = self.create_stats_display(sidebar); self.create_action_buttons(sidebar)
        self.refresh_all_ui()

    # ... create_stats_display, create_action_buttons, update_stats_display, draw methods unchanged ...

    def open_levelup_window(self, root_win):
        win = tk.Toplevel(root_win); win.title("Awans na Poziom!"); win.configure(bg="#2c2c2c"); win.grab_set()
        win.protocol("WM_DELETE_WINDOW", lambda: None) # Prevent closing without choice

        tk.Label(win, text=f"Osiągnięto Poziom {self.game_logic.player.level}!", font=self.bold_font, bg="#2c2c2c", fg="yellow").pack(pady=10)
        tk.Label(win, text="Wybierz swoją nagrodę:", font=self.bold_font, bg="#2c2c2c", fg="white").pack(pady=5)

        rewards_frame = tk.Frame(win, bg="#2c2c2c"); rewards_frame.pack(pady=10, padx=20)

        def on_choose(reward_type):
            self.game_logic.apply_levelup_reward(reward_type)
            self.update_stats_display()

            # Check for multi-level-up
            if self.game_logic.player._level_up_core():
                win.destroy()
                self.open_levelup_window(root_win)
            else:
                win.destroy()

        rewards = self.game_logic.get_levelup_rewards()
        for reward in rewards:
            btn = tk.Button(rewards_frame, text=reward["text"], command=partial(on_choose, reward["type"]), bg="#444", fg="white", relief=tk.FLAT)
            btn.pack(fill=tk.X, pady=5)
            Tooltip(btn, reward["tooltip"])

    def open_combat_window(self, enemy):
        win = tk.Toplevel(self.root); win.title(f"Walka: {enemy.name}"); win.configure(bg="#2c2c2c"); win.grab_set()
        # ... (rest of the layout from previous steps) ...
        skills_frame = tk.Frame(win, bg="#2c2c2c"); skills_frame.pack(pady=10, padx=10)
        log_text = tk.Text(win, height=10, width=60, bg="#1a1a1a", fg="white", relief=tk.FLAT, font=("Courier", 9)); log_text.pack()

        def refresh():
            # ...
            player_skills = [self.game_logic.master_skills[key] for key in self.game_logic.player.unlocked_skills]
            for skill in player_skills:
                btn = tk.Button(skills_frame, text=f"{skill.name}\n({skill.cost} SM)", command=partial(on_skill, skill), bg="#900", fg="white", relief=tk.FLAT)
                if self.game_logic.player.sm < skill.cost: btn.config(state=tk.DISABLED, bg="#555")
                btn.pack(side=tk.LEFT, padx=5, ipadx=5, ipady=2)
                Tooltip(btn, f"{skill.description}\nObrażenia: {skill.damage}")

        def on_skill(skill):
            entries, events = self.game_logic.handle_combat_turn(skill, enemy)
            for entry in entries: log.insert(tk.END, entry + "\n"); log.see(tk.END)
            if "level_up" in events:
                self.open_levelup_window(win)
            refresh()

        refresh()

    # ... all other methods are unchanged ...
    def on_save_game(self): pass
    def on_load_game(self): pass
    def open_inventory_window(self): pass
    def open_quest_log_window(self): pass
    def open_dialogue_window(self, npc): pass
    def open_skill_tree_window(self): pass
