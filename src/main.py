import tkinter as tk
from tkinter import font as tkfont
from functools import partial

# --- Data Classes ---

class Item:
    """A generic item in the inventory."""
    def __init__(self, name, description, item_type="misc"):
        self.name = name
        self.description = description
        self.item_type = item_type

class Equipment(Item):
    """An item that can be equipped to provide bonuses."""
    def __init__(self, name, description, slot, bonuses=None):
        super().__init__(name, description, item_type="equipment")
        self.slot = slot  # e.g., "Ręka", "Ciało"
        self.bonuses = bonuses if bonuses else {}

class Player:
    """Represents the player character."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.gd_max = 100
        self.gd = 100
        self.sm = 50
        self.wgk = 0
        self.damage = 10

        self.inventory = [
            Item("Rdzeń Mocażowy", "Przywraca 20 SM."),
            Equipment("Fartuch Wuja", "Zwiększa maks. GD o 20.", "Ciało", bonuses={"gd_max": 20})
        ]
        self.equipment = {"Ręka": None, "Ciało": None}

    def equip(self, item):
        if item.item_type == "equipment" and item in self.inventory:
            if self.equipment.get(item.slot):
                self.unequip(self.equipment[item.slot])

            self.inventory.remove(item)
            self.equipment[item.slot] = item

            for stat, value in item.bonuses.items():
                if hasattr(self, stat):
                    setattr(self, stat, getattr(self, stat) + value)
            self.gd = min(self.gd, self.gd_max) # Prevent health overflow on equip
            print(f"Wyposażono: {item.name}")
            return True
        return False

    def unequip(self, item):
        if item.item_type == "equipment" and item == self.equipment.get(item.slot):
            self.equipment[item.slot] = None
            self.inventory.append(item)

            for stat, value in item.bonuses.items():
                if hasattr(self, stat):
                    setattr(self, stat, getattr(self, stat) - value)
            self.gd = min(self.gd, self.gd_max) # Adjust health if max GD decreased
            print(f"Zdjęto: {item.name}")
            return True
        return False

class NPC:
    def __init__(self, x, y, name, dialogue_key):
        self.x, self.y, self.name, self.dialogue_key = x, y, name, dialogue_key

class Enemy:
    def __init__(self, x, y, name, gd, damage):
        self.x, self.y, self.name, self.gd, self.damage = x, y, name, gd, damage

# --- Game Logic ---

class GameLogic:
    def __init__(self, grid_width, grid_height):
        self.grid_width, self.grid_height = grid_width, grid_height
        self.player = Player(grid_width // 2, grid_height // 2)

        self.npcs = [
            NPC(5, 5, "Mędrzec Ji-Ae", "ji_ae_start"),
            NPC(2, 9, "Lord Bonglord", "bonglord_start")
        ]
        self.enemies = [Enemy(10, 8, "Wróg Funkcji", 50, 8)]

        self.dialogues = {
            "ji_ae_start": {
                "text": "Witaj, wędrowcze. Widzę, że twój Strumień Mocażu jest silny.",
                "options": [{"label": "Szukam wiedzy.", "next": "ji_ae_knowledge"}, {"label": "[Odejdź]", "next": "end"}]
            },
            "ji_ae_knowledge": {
                "text": "Wiedza jest jak Mocaż, potężna i niebezpieczna. Uważaj.",
                "options": [{"label": "[Dziękuję]", "next": "end"}]
            },
            "bonglord_start": {
                "text": "Czuję harmonię w twoim oddechu. To rzadkość. Ćwiczysz Gamę Wiatrów?",
                "options": [
                    {"label": "Co to jest Gama Wiatrów?", "next": "bonglord_explain"},
                    {"label": "Staram się, mistrzu.", "next": "bonglord_approve"}
                ]
            },
            "bonglord_explain": {
                "text": "To rytm 3-6. Uspokaja strumień, pozwala mierzyć bez zakłóceń. Prawda jest funkcją spokoju, nie krzyku.",
                "options": [{"label": "[Zapamiętam to]", "next": "end"}]
            },
            "bonglord_approve": {
                "text": "Dobrze. Pamiętaj: najpierw zrozum, potem nazwij. To droga szkoły Bonglord-Hazet.",
                "options": [{"label": "[Będę pamiętać]", "next": "end"}]
            }
        }

    def get_entity_at(self, x, y):
        for entity in self.npcs + self.enemies:
            if entity.x == x and entity.y == y: return entity
        return None

    def move_player_or_interact(self, target_x, target_y):
        entity = self.get_entity_at(target_x, target_y)
        if entity:
            if isinstance(entity, NPC): return ("interact", entity)
            if isinstance(entity, Enemy): return ("combat", entity)

        if not (0 <= target_x < self.grid_width and 0 <= target_y < self.grid_height):
            return ("invalid", None)

        dx, dy = abs(target_x - self.player.x), abs(target_y - self.player.y)
        if dx + dy == 1:
            self.player.x, self.player.y = target_x, target_y
            return ("move", None)
        return ("invalid", None)

    def handle_combat_turn(self, enemy):
        log = []
        enemy.gd -= self.player.damage
        log.append(f"Zadajesz {self.player.damage} obrażeń {enemy.name}.")
        if enemy.gd <= 0:
            log.append(f"{enemy.name} został pokonany!")
            self.enemies.remove(enemy)
            return log

        self.player.gd -= enemy.damage
        log.append(f"{enemy.name} rani cię za {enemy.damage} obrażeń.")
        if self.player.gd <= 0: log.append("Zostałeś pokonany...")
        return log

# --- GUI ---

class TriwersumGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Triwersum Roguelike")
        self.root.configure(bg="#1a1a1a")
        self.bold_font = tkfont.Font(family="Helvetica", size=10, weight="bold")

        self.grid_width, self.grid_height, self.cell_size = 15, 12, 40
        self.game_logic = GameLogic(self.grid_width, self.grid_height)
        self.player_rect = None
        self.entity_rects = {}

        main_frame = tk.Frame(root, bg="#1a1a1a")
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(main_frame, width=self.grid_width * self.cell_size, height=self.grid_height * self.cell_size, bg="#222", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=(0, 10))
        self.canvas.bind("<Button-1>", self.handle_map_click)

        sidebar_frame = tk.Frame(main_frame, bg="#1a1a1a")
        sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y, expand=True)

        self.stats_labels = self.create_stats_display(sidebar_frame)
        self.create_action_buttons(sidebar_frame)

        self.draw_grid()
        self.draw_entities()
        self.draw_player()
        self.update_stats_display()

    def create_stats_display(self, parent):
        stats_frame = tk.Frame(parent, bg="#2c2c2c")
        stats_frame.pack(pady=(0, 10), fill=tk.X)
        tk.Label(stats_frame, text="STATYSTYKI", font=self.bold_font, bg="#2c2c2c", fg="white").pack(pady=10, padx=10)
        labels = {}
        stats_to_display = {"GD": "Gęstość Dopy (GD)", "SM": "Strumień Mocażu (SM)", "WGK": "Gen. Kopcia (WGK)"}
        for key, text in stats_to_display.items():
            frame = tk.Frame(stats_frame, bg="#2c2c2c")
            frame.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(frame, text=f"{text}:", font=self.bold_font, bg="#2c2c2c", fg="#aaa").pack(side=tk.LEFT)
            labels[key] = tk.Label(frame, text="", font=self.bold_font, bg="#2c2c2c", fg="white")
            labels[key].pack(side=tk.RIGHT)
        return labels

    def create_action_buttons(self, parent):
        actions_frame = tk.Frame(parent, bg="#2c2c2c")
        actions_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(actions_frame, text="AKCJE", font=self.bold_font, bg="#2c2c2c", fg="white").pack(pady=10)
        tk.Button(actions_frame, text="Ekwipunek", command=self.open_inventory_window, bg="#444", fg="white", relief=tk.FLAT).pack(pady=5, padx=10, fill=tk.X)

    def update_stats_display(self):
        p = self.game_logic.player
        self.stats_labels["GD"].config(text=f"{p.gd}/{p.gd_max}")
        self.stats_labels["SM"].config(text=str(p.sm))
        self.stats_labels["WGK"].config(text=str(p.wgk))

    def draw_grid(self):
        for i in range(self.grid_width + 1): self.canvas.create_line(i * self.cell_size, 0, i * self.cell_size, self.grid_height * self.cell_size, fill="#444")
        for i in range(self.grid_height + 1): self.canvas.create_line(0, i * self.cell_size, self.grid_width * self.cell_size, i * self.cell_size, fill="#444")

    def draw_player(self):
        if self.player_rect: self.canvas.delete(self.player_rect)
        x1, y1 = self.game_logic.player.x * self.cell_size, self.game_logic.player.y * self.cell_size
        self.player_rect = self.canvas.create_rectangle(x1, y1, x1 + self.cell_size, y1 + self.cell_size, fill="blue", outline="lightblue", width=2)

    def draw_entities(self):
        for name, rect in self.entity_rects.items(): self.canvas.delete(rect)
        self.entity_rects.clear()
        for entity in self.game_logic.npcs + self.game_logic.enemies:
            color = "green" if isinstance(entity, NPC) else "red"
            x1, y1 = entity.x * self.cell_size, entity.y * self.cell_size
            rect = self.canvas.create_rectangle(x1, y1, x1 + self.cell_size, y1 + self.cell_size, fill=color, outline=f"light{color}", width=2)
            self.entity_rects[entity.name] = rect

    def handle_map_click(self, event):
        clicked_x, clicked_y = event.x // self.cell_size, event.y // self.cell_size
        action, data = self.game_logic.move_player_or_interact(clicked_x, clicked_y)
        if action == "move": self.draw_player()
        elif action == "interact": self.open_dialogue_window(data)
        elif action == "combat": self.open_combat_window(data)
        self.update_stats_display()

    def open_inventory_window(self):
        inv_win = tk.Toplevel(self.root)
        inv_win.title("Ekwipunek")
        inv_win.configure(bg="#2c2c2c")
        inv_win.grab_set()

        def refresh_inventory():
            for widget in inv_win.winfo_children(): widget.destroy()

            tk.Label(inv_win, text="-- WYPOSAŻONE --", font=self.bold_font, bg="#2c2c2c", fg="white").pack(pady=5)
            for slot, item in self.game_logic.player.equipment.items():
                text = f"{slot}: {item.name if item else 'Pusty'}"
                frame = tk.Frame(inv_win, bg="#2c2c2c")
                frame.pack(padx=10, fill=tk.X)
                tk.Label(frame, text=text, bg="#2c2c2c", fg="white").pack(side=tk.LEFT)
                if item: tk.Button(frame, text="Zdejmij", command=partial(self.on_unequip, item, refresh_inventory), bg="#555", fg="white", relief=tk.FLAT).pack(side=tk.RIGHT)

            tk.Label(inv_win, text="-- PLECAK --", font=self.bold_font, bg="#2c2c2c", fg="white").pack(pady=5)
            for item in self.game_logic.player.inventory:
                frame = tk.Frame(inv_win, bg="#2c2c2c")
                frame.pack(padx=10, fill=tk.X)
                tk.Label(frame, text=item.name, bg="#2c2c2c", fg="white").pack(side=tk.LEFT)
                if item.item_type == "equipment": tk.Button(frame, text="Wyposaż", command=partial(self.on_equip, item, refresh_inventory), bg="#444", fg="white", relief=tk.FLAT).pack(side=tk.RIGHT)

        refresh_inventory()

    def on_equip(self, item, refresh_callback):
        if self.game_logic.player.equip(item):
            self.update_stats_display()
            refresh_callback()

    def on_unequip(self, item, refresh_callback):
        if self.game_logic.player.unequip(item):
            self.update_stats_display()
            refresh_callback()

    def open_dialogue_window(self, npc): # Simplified for brevity, logic is the same
        dialogue_win = tk.Toplevel(self.root); dialogue_win.title(f"Rozmowa z {npc.name}"); dialogue_win.grab_set()
        # ... dialogue logic from previous step ...
        content = self.game_logic.dialogues.get(npc.dialogue_key)
        tk.Label(dialogue_win, text=content['text'], wraplength=300).pack(padx=10, pady=10)
        tk.Button(dialogue_win, text="[Zamknij]", command=dialogue_win.destroy).pack(pady=5)


    def open_combat_window(self, enemy): # Simplified for brevity, logic is the same
        combat_win = tk.Toplevel(self.root); combat_win.title(f"Walka: {enemy.name}"); combat_win.grab_set()
        # ... combat logic from previous step ...
        def on_attack():
            log = self.game_logic.handle_combat_turn(enemy)
            if enemy.gd <= 0: self.draw_entities()
            if self.game_logic.player.gd <= 0 or enemy.gd <= 0: attack_button.config(state=tk.DISABLED)
            self.update_stats_display()
        attack_button = tk.Button(combat_win, text="Atakuj", command=on_attack)
        attack_button.pack(pady=10)

def main():
    try:
        root = tk.Tk()
        game = TriwersumGame(root)
        root.mainloop()
    except tk.TclError:
        print("Could not open display. This is expected in a headless environment.")

if __name__ == "__main__":
    main()
