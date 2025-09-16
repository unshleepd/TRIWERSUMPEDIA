import tkinter as tk
from tkinter import font as tkfont, messagebox
from functools import partial
from game_logic import GameLogic
from data_classes import NPC, Enemy

class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT, background="#FFFFE0", relief=tk.SOLID, borderwidth=1, wraplength=180)
        label.pack(ipadx=1)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
        self.tooltip_window = None

class TriwersumGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Triwersum Roguelike")
        self.root.configure(bg="#1a1a1a")
        self.bold_font = tkfont.Font(family="Helvetica", size=10, weight="bold")
        self.map_font = tkfont.Font(family="Courier", size=20, weight="bold")
        self.grid_width, self.grid_height, self.cell_size = 15, 12, 40
        self.game_logic = GameLogic(self.grid_width, self.grid_height)
        self.player_text_id, self.entity_text_ids = None, {}
        main_frame = tk.Frame(root, bg="#1a1a1a")
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(main_frame, width=self.grid_width * self.cell_size, height=self.grid_height * self.cell_size, bg="#222", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=(0, 10))
        self.canvas.bind("<Button-1>", self.handle_map_click)
        sidebar = tk.Frame(main_frame, bg="#1a1a1a")
        sidebar.pack(side=tk.RIGHT, fill=tk.Y, expand=True)
        self.stats_labels = self.create_stats_display(sidebar)
        self.create_action_buttons(sidebar)
        self.refresh_all_ui()

    def create_stats_display(self, parent):
        frame = tk.Frame(parent, bg="#2c2c2c")
        frame.pack(pady=(0, 10), fill=tk.X)
        tk.Label(frame, text="STATYSTYKI", font=self.bold_font, bg="#2c2c2c", fg="white").pack(pady=10)
        labels = {}
        for k, t in {"LVL": "Poziom", "XP": "XP", "GD": "GD", "SM": "SM", "WGK": "WGK"}.items():
            f = tk.Frame(frame, bg="#2c2c2c")
            f.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(f, text=f"{t}:", font=self.bold_font, bg="#2c2c2c", fg="#aaa").pack(side=tk.LEFT)
            labels[k] = tk.Label(f, text="", font=self.bold_font, bg="#2c2c2c", fg="white")
            labels[k].pack(side=tk.RIGHT)
        return labels

    def create_action_buttons(self, parent):
        frame = tk.Frame(parent, bg="#2c2c2c")
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="AKCJE", font=self.bold_font, bg="#2c2c2c", fg="white").pack(pady=10)
        tk.Button(frame, text="Zapisz Grę", command=self.on_save_game, bg="#444", fg="white", relief=tk.FLAT).pack(pady=5, padx=10, fill=tk.X)
        tk.Button(frame, text="Wczytaj Grę", command=self.on_load_game, bg="#444", fg="white", relief=tk.FLAT).pack(pady=5, padx=10, fill=tk.X)
        tk.Button(frame, text="Ekwipunek", command=self.open_inventory_window, bg="#444", fg="white", relief=tk.FLAT).pack(pady=5, padx=10, fill=tk.X)
        tk.Button(frame, text="Questy", command=self.open_quest_log_window, bg="#444", fg="white", relief=tk.FLAT).pack(pady=5, padx=10, fill=tk.X)

    def update_stats_display(self):
        p = self.game_logic.player
        self.stats_labels["LVL"].config(text=str(p.level))
        self.stats_labels["XP"].config(text=f"{p.xp}/{p.xp_to_next_level}")
        self.stats_labels["GD"].config(text=f"{p.gd}/{p.gd_max}")
        self.stats_labels["SM"].config(text=f"{p.sm}/{p.sm_max}")
        self.stats_labels["WGK"].config(text=str(p.wgk))

    def draw_map(self):
        self.canvas.delete("map_tile")
        for x in range(self.grid_width):
            for y in range(self.grid_height):
                tile_type = self.game_logic.map_layout[x][y]
                color = "#282828" if tile_type == 1 else "#555"
                self.canvas.create_rectangle(x * self.cell_size, y * self.cell_size, (x + 1) * self.cell_size, (y + 1) * self.cell_size, fill=color, outline="")

    def draw_player(self):
        if self.player_text_id:
            self.canvas.delete(self.player_text_id)
        p = self.game_logic.player
        x, y = (p.x + 0.5) * self.cell_size, (p.y + 0.5) * self.cell_size
        self.player_text_id = self.canvas.create_text(x, y, text=p.icon, fill=p.color, font=self.map_font)

    def draw_entities(self):
        for name in self.entity_text_ids:
            self.canvas.delete(self.entity_text_ids[name])
        self.entity_text_ids.clear()
        for entity in self.game_logic.npcs + self.game_logic.enemies:
            color = "green" if isinstance(entity, NPC) else "#E06666"
            x, y = (entity.x + 0.5) * self.cell_size, (entity.y + 0.5) * self.cell_size
            text_id = self.canvas.create_text(x, y, text=entity.icon, fill=color, font=self.map_font)
            self.entity_text_ids[entity.name] = text_id

    def refresh_all_ui(self):
        self.draw_map()
        self.draw_entities()
        self.draw_player()
        self.update_stats_display()

    def handle_map_click(self, event):
        action, data = self.game_logic.move_player_or_interact(event.x // self.cell_size, event.y // self.cell_size)
        if action == "move":
            self.draw_player()
        elif action == "interact":
            self.open_dialogue_window(data)
        elif action == "combat":
            self.open_combat_window(data)
        self.update_stats_display()

    def on_save_game(self):
        self.game_logic.save_game()
        messagebox.showinfo("Zapisano", "Gra została pomyślnie zapisana.")

    def on_load_game(self):
        if self.game_logic.load_game():
            self.refresh_all_ui()
            messagebox.showinfo("Wczytano", "Gra została pomyślnie wczytana.")
        else:
            messagebox.showwarning("Błąd", "Nie znaleziono pliku zapisu.")

    def open_inventory_window(self):
        win = tk.Toplevel(self.root); win.title("Ekwipunek"); win.configure(bg="#2c2c2c"); win.grab_set()
        def refresh():
            for w in win.winfo_children(): w.destroy()
            tk.Label(win, text="-- WYPOSAŻONE --", font=self.bold_font, bg="#2c2c2c", fg="white").pack(pady=5)
            for slot, item in self.game_logic.player.equipment.items():
                f = tk.Frame(win, bg="#2c2c2c"); f.pack(padx=10, fill=tk.X, pady=2)
                item_label = tk.Label(f, text=f"{slot}: {item.name if item else 'Pusty'}", bg="#2c2c2c", fg="white"); item_label.pack(side=tk.LEFT)
                if item: Tooltip(item_label, item.description); tk.Button(f, text="Zdejmij", command=partial(self.on_unequip, item, refresh), bg="#555", fg="white", relief=tk.FLAT).pack(side=tk.RIGHT)
            tk.Label(win, text="-- PLECAK --", font=self.bold_font, bg="#2c2c2c", fg="white").pack(pady=10)
            for item in self.game_logic.player.inventory:
                f = tk.Frame(win, bg="#2c2c2c"); f.pack(padx=10, fill=tk.X, pady=2)
                item_label = tk.Label(f, text=item.name, bg="#2c2c2c", fg="white"); item_label.pack(side=tk.LEFT)
                Tooltip(item_label, item.description)
                if item.item_type == "equipment": tk.Button(f, text="Wyposaż", command=partial(self.on_equip, item, refresh), bg="#444", fg="white", relief=tk.FLAT).pack(side=tk.RIGHT)
        refresh()

    def on_equip(self, item, cb):
        if self.game_logic.player.equip(item): self.update_stats_display(); cb()
    def on_unequip(self, item, cb):
        if self.game_logic.player.unequip(item): self.update_stats_display(); cb()

    def open_quest_log_window(self):
        win = tk.Toplevel(self.root); win.title("Dziennik Questów"); win.configure(bg="#2c2c2c"); win.grab_set()
        if not self.game_logic.player.quest_journal: tk.Label(win, text="Brak aktywnych questów.", font=self.bold_font, bg="#2c2c2c", fg="white").pack(pady=20, padx=20)
        for quest in self.game_logic.player.quest_journal.values():
            color = {"active": "yellow", "completed": "lightgreen", "rewarded": "lightblue"}.get(quest.status, "white")
            f = tk.Frame(win, bg="#444", bd=1, relief=tk.RIDGE); f.pack(pady=5, padx=10, fill=tk.X)
            tk.Label(f, text=f"{quest.title} [{quest.status.upper()}]", font=self.bold_font, bg="#444", fg=color).pack(anchor="w")
            for obj in quest.objectives: tk.Label(f, text=f"- {obj.description}", bg="#444", fg="lightgreen" if obj.is_done else "white").pack(anchor="w")

    def open_dialogue_window(self, npc):
        win = tk.Toplevel(self.root); win.title(f"Rozmowa z {npc.name}"); win.configure(bg="#2c2c2c"); win.grab_set()
        def display(key):
            for w in win.winfo_children(): w.destroy()
            content = self.game_logic.dialogues.get(key)
            if not content: win.destroy(); return
            tk.Label(win, text=content["text"], wraplength=350, justify=tk.LEFT, bg="#2c2c2c", fg="white", font=("Helvetica",12)).pack(pady=15, padx=15)
            frame = tk.Frame(win, bg="#2c2c2c"); frame.pack(pady=10)
            for option in content["options"]:
                if "condition" in option and not option["condition"](): continue
                def on_click(o=option):
                    if o.get("action") == "start_quest": self.game_logic.start_quest(o["quest_key"])
                    elif o.get("action") == "update_quest": self.game_logic.update_quest_progress("talk_to", o["target"])
                    elif o.get("action") == "grant_reward":
                        q = self.game_logic.player.quest_journal.get(o["quest_key"])
                        if q and q.reward and q.status != "rewarded": self.game_logic.player.add_item(self.game_logic.items[q.reward["key"]]); q.status = "rewarded"
                    if o["next"] == "end": win.destroy()
                    else: display(o["next"])
                tk.Button(frame, text=option["label"], command=on_click, bg="#444", fg="white", relief=tk.FLAT).pack(fill=tk.X, pady=2, padx=10)
        display(npc.dialogue_key)

    def open_combat_window(self, enemy):
        win = tk.Toplevel(self.root); win.title(f"Walka: {enemy.name}"); win.configure(bg="#2c2c2c"); win.grab_set()
        stats_frame = tk.Frame(win, bg="#2c2c2c"); stats_frame.pack(pady=10, padx=10, fill=tk.X, expand=True)
        log_frame = tk.Frame(win, bg="#2c2c2c"); log_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        skills_frame = tk.Frame(win, bg="#2c2c2c"); skills_frame.pack(pady=10, padx=10)
        player_frame = tk.Frame(stats_frame, bg="#3c3c3c", bd=2, relief=tk.RIDGE); player_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        enemy_frame = tk.Frame(stats_frame, bg="#3c3c3c", bd=2, relief=tk.RIDGE); enemy_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        tk.Label(player_frame, text="Gracz", font=self.bold_font, bg="#3c3c3c", fg="white").pack()
        player_hp_label = tk.Label(player_frame, font=self.bold_font, bg="#3c3c3c", fg="white"); player_hp_label.pack()
        tk.Label(enemy_frame, text=enemy.name, font=self.bold_font, bg="#3c3c3c", fg="white").pack()
        enemy_hp_label = tk.Label(enemy_frame, font=self.bold_font, bg="#3c3c3c", fg="white"); enemy_hp_label.pack()
        log_text = tk.Text(log_frame, height=10, width=60, bg="#1a1a1a", fg="white", relief=tk.FLAT, font=("Courier", 9)); log_text.pack()
        log_text.insert(tk.END, f"Napotykasz {enemy.name}!\n")
        def refresh():
            p = self.game_logic.player
            player_hp_label.config(text=f"GD: {p.gd}/{p.gd_max}")
            enemy_hp_label.config(text=f"GD: {enemy.gd if enemy.gd > 0 else 0}")
            self.update_stats_display()
            for w in skills_frame.winfo_children(): w.destroy()
            if p.gd <= 0 or enemy not in self.game_logic.enemies:
                tk.Button(skills_frame, text="Zakończ", command=win.destroy, bg="#444", fg="white", relief=tk.FLAT).pack()
                self.draw_entities()
            else:
                for skill in p.skills:
                    btn = tk.Button(skills_frame, text=f"{skill.name}\n({skill.cost} SM)", command=partial(on_skill, skill), bg="#900", fg="white", relief=tk.FLAT)
                    if p.sm < skill.cost: btn.config(state=tk.DISABLED, bg="#555")
                    btn.pack(side=tk.LEFT, padx=5, ipadx=5, ipady=2)
                    Tooltip(btn, f"{skill.description}\nObrażenia: {skill.damage}")
        def on_skill(skill):
            entries, events = self.game_logic.handle_combat_turn(skill, enemy)
            for entry in entries: log.insert(tk.END, entry + "\n"); log.see(tk.END)
            if "level_up" in events: self.open_levelup_window(win)
            refresh()
        refresh()

    def open_levelup_window(self, root_win):
        win = tk.Toplevel(root_win); win.title("Awans na Poziom!"); win.configure(bg="#2c2c2c"); win.grab_set()
        win.protocol("WM_DELETE_WINDOW", lambda: None)
        tk.Label(win, text=f"Osiągnięto Poziom {self.game_logic.player.level}!", font=self.bold_font, bg="#2c2c2c", fg="yellow").pack(pady=10)
        tk.Label(win, text="Wybierz swoją nagrodę:", font=self.bold_font, bg="#2c2c2c", fg="white").pack(pady=5)
        rewards_frame = tk.Frame(win, bg="#2c2c2c"); rewards_frame.pack(pady=10, padx=20)
        def on_choose(reward):
            self.game_logic.apply_levelup_reward(reward["type"], reward.get("value"))
            self.update_stats_display()
            if self.game_logic.player._level_up_core():
                win.destroy(); self.open_levelup_window(root_win)
            else:
                win.destroy()
        rewards = self.game_logic.get_levelup_rewards()
        for reward in rewards:
            btn = tk.Button(rewards_frame, text=reward["text"], command=partial(on_choose, reward), bg="#444", fg="white", relief=tk.FLAT)
            btn.pack(fill=tk.X, pady=5)
            Tooltip(btn, reward["tooltip"])
