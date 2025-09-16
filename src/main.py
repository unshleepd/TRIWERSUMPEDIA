import tkinter as tk
from tkinter import font as tkfont, messagebox
from functools import partial
import json
import os

SAVE_FILE = "savegame.json"

# --- Data Classes ---
class Skill:
    def __init__(self, name, cost, damage, description=""): self.name, self.cost, self.damage, self.description = name, cost, damage, description
class Objective:
    def __init__(self, description, target_type, target_name): self.description, self.target_type, self.target_name, self.is_done = description, target_type, target_name, False
    def to_dict(self): return self.is_done
    @classmethod
    def from_dict(cls, data, description, target_type, target_name): obj = cls(description, target_type, target_name); obj.is_done = data; return obj
class Quest:
    def __init__(self, key, title, description, objectives, reward=None): self.key, self.title, self.description, self.objectives, self.reward, self.status = key, title, description, objectives, reward, "inactive"
    def to_dict(self): return {"status": self.status, "objectives": [obj.to_dict() for obj in self.objectives]}
    @classmethod
    def from_dict(cls, data, key, title, description, objectives, reward=None):
        quest = cls(key, title, description, [Objective.from_dict(d, o.description, o.target_type, o.target_name) for d, o in zip(data["objectives"], objectives)], reward)
        quest.status = data["status"]; return quest
class Item:
    def __init__(self, name, description, item_type="misc"): self.name, self.description, self.item_type = name, description, item_type
    def to_dict(self): return {"name": self.name, "type": self.item_type}
class Equipment(Item):
    def __init__(self, name, description, slot, bonuses=None): super().__init__(name, description, item_type="equipment"); self.slot, self.bonuses = slot, bonuses if bonuses else {}
    def to_dict(self): data = super().to_dict(); data.update({"slot": self.slot, "bonuses": self.bonuses}); return data

class Player:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.gd_max, self.gd, self.sm_max, self.sm, self.wgk = 100, 100, 50, 50, 0
        self.level, self.xp, self.xp_to_next_level = 1, 0, 100
        self.inventory = [Equipment("Fartuch Wuja", "Zwiększa maks. GD o 20.", "Ciało", bonuses={"gd_max": 20})]
        self.equipment = {"Ręka": None, "Ciało": None}
        self.quest_journal = {}
        self.skills = [Skill("Zwykły Atak", 0, 8), Skill("Harmoniczne Uderzenie", 10, 20)]
    def to_dict(self):
        return {"x": self.x, "y": self.y, "gd_max": self.gd_max, "gd": self.gd, "sm_max": self.sm_max, "sm": self.sm, "level": self.level, "xp": self.xp, "xp_to_next_level": self.xp_to_next_level, "inventory": [item.to_dict() for item in self.inventory], "equipment": {slot: item.to_dict() if item else None for slot, item in self.equipment.items()}, "quest_journal": {key: quest.to_dict() for key, quest in self.quest_journal.items()}}
    def _level_up(self):
        self.xp -= self.xp_to_next_level
        self.level += 1
        self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
        self.gd_max += 10
        self.sm_max += 5
        self.gd = self.gd_max
        self.sm = self.sm_max
    def add_xp(self, amount):
        self.xp += amount
        leveled_up = False
        while self.xp >= self.xp_to_next_level:
            self._level_up()
            leveled_up = True
        return leveled_up
    def add_quest(self, quest):
        if quest.key not in self.quest_journal: quest.status = "active"; self.quest_journal[quest.key] = quest
    def add_item(self, item): self.inventory.append(item)
    def equip(self, item):
        if item.item_type == "equipment" and item in self.inventory:
            if self.equipment.get(item.slot): self.unequip(self.equipment[item.slot])
            self.inventory.remove(item)
            self.equipment[item.slot] = item
            for stat, value in item.bonuses.items(): setattr(self, stat, getattr(self, stat) + value)
            self.gd = min(self.gd, self.gd_max)
            return True
        return False
    def unequip(self, item):
        if item.item_type == "equipment" and item == self.equipment.get(item.slot):
            self.equipment[item.slot] = None
            self.inventory.append(item)
            for stat, value in item.bonuses.items(): setattr(self, stat, getattr(self, stat) - value)
            self.gd = min(self.gd, self.gd_max)
            return True
        return False

class NPC:
    def __init__(self, x, y, name, dialogue_key): self.x, self.y, self.name, self.dialogue_key = x, y, name, dialogue_key
class Enemy:
    def __init__(self, x, y, name, gd, skills, xp_reward): self.x, self.y, self.name, self.gd, self.skills, self.xp_reward = x, y, name, gd, skills, xp_reward
    def to_dict(self): return {"name": self.name, "x": self.x, "y": self.y, "gd": self.gd}

# --- Game Logic ---

class GameLogic:
    def __init__(self, grid_width, grid_height): self.grid_width, self.grid_height = grid_width, grid_height; self.initialize_game_state()
    def initialize_game_state(self, from_save=None):
        self.items = {"kleszcze": Equipment("Kleszcze Króla Dzwonów", "Zwiększa maks. SM o 15.", "Ręka", bonuses={"sm_max": 15}), "fartuch": Equipment("Fartuch Wuja", "Zwiększa maks. GD o 20.", "Ciało", bonuses={"gd_max": 20})}
        self.static_npcs = [NPC(5, 5, "Mędrzec Ji-Ae", "ji_ae_start"), NPC(2, 9, "Lord Bonglord", "bonglord_start")]
        self.static_enemies = {"Wróg Funkcji": (50, [Skill("Cios Funkcyjny", 0, 8)], 40), "Siewca Paradygmatu": (80, [Skill("Cios Paradygmatu", 0, 12)], 75)}
        self.quests = {"bonglord_quest": Quest("bonglord_quest", "Próba Harmonii", "Pomóż Lordowi Bonglordowi.", [Objective("Porozmawiaj z Mędrcem Ji-Ae", "talk_to", "Mędrzec Ji-Ae"), Objective("Pokonaj Siewcę Paradygmatu", "defeat", "Siewca Paradygmatu")], reward={"type": "item", "key": "kleszcze"})}
        if from_save: self.load_from_state(from_save)
        else:
            self.player = Player(self.grid_width // 2, self.grid_height // 2)
            self.npcs = list(self.static_npcs)
            self.enemies = [Enemy(10, 8, "Wróg Funkcji", 50, [Skill("Cios Funkcyjny", 0, 8)], 40), Enemy(12, 2, "Siewca Paradygmatu", 80, [Skill("Cios Paradygmatu", 0, 12)], 75)]
        self.dialogues = self.get_dialogues()
    def get_save_state(self): return {"player": self.player.to_dict(), "enemies": [e.to_dict() for e in self.enemies]}
    def load_from_state(self, state):
        p_data = state["player"]; self.player = Player(p_data["x"], p_data["y"])
        for key in ["gd_max", "gd", "sm_max", "sm", "level", "xp", "xp_to_next_level"]: setattr(self.player, key, p_data[key])
        self.player.inventory = [self.rebuild_item(item_data) for item_data in p_data["inventory"]]
        self.player.equipment = {slot: self.rebuild_item(item_data) if item_data else None for slot, item_data in p_data["equipment"].items()}
        self.player.quest_journal = {key: Quest.from_dict(q_data, **self.quests[key].__dict__) for key, q_data in p_data["quest_journal"].items()}
        self.enemies = []
        for e_data in state["enemies"]:
            name, gd, skills, xp = e_data["name"], e_data["gd"], self.static_enemies[e_data["name"]][1], self.static_enemies[e_data["name"]][2]
            self.enemies.append(Enemy(e_data["x"], e_data["y"], name, gd, skills, xp))
    def rebuild_item(self, item_data):
        for item in self.items.values():
            if item.name == item_data["name"]: return Equipment(item.name, item.description, item.slot, item.bonuses)
        return Item(item_data.get("name", "Unknown"), "Unknown")
    def save_game(self):
        with open(SAVE_FILE, 'w') as f: json.dump(self.get_save_state(), f, indent=4)
    def load_game(self):
        if not os.path.exists(SAVE_FILE): return False
        with open(SAVE_FILE, 'r') as f: state = json.load(f)
        self.initialize_game_state(from_save=state); return True
    def get_entity_at(self, x, y):
        for entity in self.npcs + self.enemies:
            if entity.x == x and entity.y == y: return entity
        return None
    def move_player_or_interact(self, target_x, target_y):
        entity = self.get_entity_at(target_x, target_y)
        if entity:
            if isinstance(entity, NPC): return ("interact", entity)
            if isinstance(entity, Enemy): return ("combat", entity)
        if 0 <= target_x < self.grid_width and 0 <= target_y < self.grid_height and abs(target_x - self.player.x) + abs(target_y - self.player.y) == 1:
            self.player.x, self.player.y = target_x, target_y
            return ("move", None)
        return ("invalid", None)
    def handle_combat_turn(self, player_skill, enemy):
        log, events = [], []
        if self.player.sm < player_skill.cost: log.append("Brak Strumienia Mocażu!"); return log, events
        self.player.sm -= player_skill.cost
        enemy.gd -= player_skill.damage
        log.append(f"Używasz '{player_skill.name}' i zadajesz {player_skill.damage} obrażeń.")
        if enemy.gd <= 0:
            log.append(f"{enemy.name} został pokonany!")
            if self.player.add_xp(enemy.xp_reward): events.append("level_up")
            self.update_quest_progress("defeat", enemy.name)
            self.enemies.remove(enemy)
            return log, events
        enemy_skill = enemy.skills[0]
        self.player.gd -= enemy_skill.damage
        log.append(f"{enemy.name} używa '{enemy_skill.name}' i rani cię za {enemy_skill.damage} obrażeń.")
        if self.player.gd <= 0: log.append("Zostałeś pokonany...")
        return log, events
    def start_quest(self, key):
        if key in self.quests: self.player.add_quest(self.quests[key])
    def update_quest_progress(self, event_type, target_name):
        for quest in self.player.quest_journal.values():
            if quest.status == "active":
                for obj in quest.objectives:
                    if obj.target_type == event_type and obj.target_name == target_name: obj.is_done = True
                if all(obj.is_done for obj in quest.objectives): quest.status = "completed"
    def get_dialogues(self):
        return {"ji_ae_start": {"text": "Witaj, wędrowcze.", "options": [{"label": "Lord Bonglord mnie przysyła.", "next": "ji_ae_quest_talk", "condition": lambda: self.player.quest_journal.get("bonglord_quest", {}).status == "active"}, {"label": "[Odejdź]", "next": "end"}]}, "ji_ae_quest_talk": {"text": "Ach, więc to o to chodzi. Siewca Paradygmatu na północy... Jest potężny. Uważaj.", "options": [{"label": "[Dziękuję za ostrzeżenie]", "next": "end", "action": "update_quest", "target": "Mędrzec Ji-Ae"}]}, "bonglord_start": {"text": "Czuję harmonię w twoim oddechu. Ale coś zakłóca przepływy...", "options": [{"label": "Co masz na myśli?", "next": "bonglord_quest_offer", "condition": lambda: self.player.quest_journal.get("bonglord_quest") is None}, {"label": "Wróciłem, mistrzu.", "next": "bonglord_reward", "condition": lambda: self.player.quest_journal.get("bonglord_quest", {}).status == "completed"}, {"label": "[Odejdź]", "next": "end"}]}, "bonglord_quest_offer": {"text": "Siewca Paradygmatu mąci na północy. Porozmawiaj z Ji-Ae, a potem go pokonaj. Zostaniesz nagrodzony.", "options": [{"label": "Zgoda.", "next": "end", "action": "start_quest", "quest_key": "bonglord_quest"}, {"label": "Nie teraz.", "next": "end"}]}, "bonglord_reward": {"text": "Wykonałeś zadanie. Równowaga wraca. Przyjmij ten dar.", "options": [{"label": "[Weź nagrodę]", "next": "end", "action": "grant_reward", "quest_key": "bonglord_quest"}]}}

# --- GUI ---

class TriwersumGame:
    def __init__(self, root):
        self.root = root; self.root.title("Triwersum Roguelike"); self.root.configure(bg="#1a1a1a")
        self.bold_font = tkfont.Font(family="Helvetica", size=10, weight="bold")
        self.grid_width, self.grid_height, self.cell_size = 15, 12, 40
        self.game_logic = GameLogic(self.grid_width, self.grid_height)
        self.player_rect, self.entity_rects = None, {}
        main_frame = tk.Frame(root, bg="#1a1a1a"); main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(main_frame, width=self.grid_width*self.cell_size, height=self.grid_height*self.cell_size, bg="#222", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=(0, 10)); self.canvas.bind("<Button-1>", self.handle_map_click)
        sidebar = tk.Frame(main_frame, bg="#1a1a1a"); sidebar.pack(side=tk.RIGHT, fill=tk.Y, expand=True)
        self.stats_labels = self.create_stats_display(sidebar); self.create_action_buttons(sidebar)
        self.refresh_all_ui()
    def create_stats_display(self, parent):
        frame = tk.Frame(parent, bg="#2c2c2c"); frame.pack(pady=(0, 10), fill=tk.X)
        tk.Label(frame, text="STATYSTYKI", font=self.bold_font, bg="#2c2c2c", fg="white").pack(pady=10)
        labels = {}
        for k, t in {"LVL": "Poziom", "XP": "XP", "GD": "GD", "SM": "SM", "WGK": "WGK"}.items():
            f = tk.Frame(frame, bg="#2c2c2c"); f.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(f, text=f"{t}:", font=self.bold_font, bg="#2c2c2c", fg="#aaa").pack(side=tk.LEFT)
            labels[k] = tk.Label(f, text="", font=self.bold_font, bg="#2c2c2c", fg="white"); labels[k].pack(side=tk.RIGHT)
        return labels
    def create_action_buttons(self, parent):
        frame = tk.Frame(parent, bg="#2c2c2c"); frame.pack(fill=tk.BOTH, expand=True)
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
    def draw_grid(self):
        for i in range(self.grid_width+1): self.canvas.create_line(i*self.cell_size,0,i*self.cell_size,self.grid_height*self.cell_size,fill="#444")
        for i in range(self.grid_height+1): self.canvas.create_line(0,i*self.cell_size,self.grid_width*self.cell_size,i*self.cell_size,fill="#444")
    def draw_player(self):
        if self.player_rect: self.canvas.delete(self.player_rect)
        x1, y1 = self.game_logic.player.x*self.cell_size, self.game_logic.player.y*self.cell_size
        self.player_rect = self.canvas.create_rectangle(x1, y1, x1+self.cell_size, y1+self.cell_size, fill="blue", outline="lightblue", width=2)
    def draw_entities(self):
        for name in self.entity_rects: self.canvas.delete(self.entity_rects[name])
        self.entity_rects.clear()
        for entity in self.game_logic.npcs + self.game_logic.enemies:
            color = "green" if isinstance(entity, NPC) else "red"
            x1, y1 = entity.x*self.cell_size, entity.y*self.cell_size
            rect = self.canvas.create_rectangle(x1, y1, x1+self.cell_size, y1+self.cell_size, fill=color, outline=f"light{color}", width=2)
            self.entity_rects[entity.name] = rect
    def refresh_all_ui(self):
        self.draw_grid(); self.draw_entities(); self.draw_player(); self.update_stats_display()
    def handle_map_click(self, event):
        action, data = self.game_logic.move_player_or_interact(event.x//self.cell_size, event.y//self.cell_size)
        if action == "move": self.draw_player()
        elif action == "interact": self.open_dialogue_window(data)
        elif action == "combat": self.open_combat_window(data)
        self.update_stats_display()
    def on_save_game(self): self.game_logic.save_game(); messagebox.showinfo("Zapisano", "Gra została pomyślnie zapisana.")
    def on_load_game(self):
        if self.game_logic.load_game(): self.refresh_all_ui(); messagebox.showinfo("Wczytano", "Gra została pomyślnie wczytana.")
        else: messagebox.showwarning("Błąd", "Nie znaleziono pliku zapisu.")
    def open_inventory_window(self):
        win = tk.Toplevel(self.root); win.title("Ekwipunek"); win.configure(bg="#2c2c2c"); win.grab_set()
        def refresh():
            for w in win.winfo_children(): w.destroy()
            tk.Label(win, text="-- WYPOSAŻONE --", font=self.bold_font, bg="#2c2c2c", fg="white").pack(pady=5)
            for slot, item in self.game_logic.player.equipment.items():
                f = tk.Frame(win, bg="#2c2c2c"); f.pack(padx=10, fill=tk.X)
                tk.Label(f, text=f"{slot}: {item.name if item else 'Pusty'}", bg="#2c2c2c", fg="white").pack(side=tk.LEFT)
                if item: tk.Button(f, text="Zdejmij", command=partial(self.on_unequip, item, refresh), bg="#555", fg="white", relief=tk.FLAT).pack(side=tk.RIGHT)
            tk.Label(win, text="-- PLECAK --", font=self.bold_font, bg="#2c2c2c", fg="white").pack(pady=5)
            for item in self.game_logic.player.inventory:
                f = tk.Frame(win, bg="#2c2c2c"); f.pack(padx=10, fill=tk.X)
                tk.Label(f, text=item.name, bg="#2c2c2c", fg="white").pack(side=tk.LEFT)
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
        info = tk.Frame(win, bg="#2c2c2c"); info.pack(pady=10, padx=10, fill=tk.X)
        player_hp = tk.Label(info, font=self.bold_font, bg="#2c2c2c", fg="white"); player_hp.pack()
        enemy_hp = tk.Label(info, font=self.bold_font, bg="#2c2c2c", fg="white"); enemy_hp.pack()
        log = tk.Text(win, height=8, width=60, bg="#1a1a1a", fg="white", relief=tk.FLAT, font=("Courier", 9)); log.pack(pady=10, padx=10)
        skills_frame = tk.Frame(win, bg="#2c2c2c"); skills_frame.pack(pady=10)
        def refresh():
            p = self.game_logic.player
            player_hp.config(text=f"Twoje GD: {p.gd}/{p.gd_max}")
            enemy_hp.config(text=f"GD Wroga: {enemy.gd if enemy.gd > 0 else 0}")
            self.update_stats_display()
            for w in skills_frame.winfo_children(): w.destroy()
            if p.gd <= 0 or enemy not in self.game_logic.enemies:
                tk.Button(skills_frame, text="Zakończ", command=win.destroy, bg="#444", fg="white", relief=tk.FLAT).pack()
                self.draw_entities()
            else:
                for skill in p.skills:
                    btn = tk.Button(skills_frame, text=f"{skill.name} ({skill.cost} SM)", command=partial(on_skill, skill), bg="#900", fg="white", relief=tk.FLAT)
                    if p.sm < skill.cost: btn.config(state=tk.DISABLED, bg="#555")
                    btn.pack(side=tk.LEFT, padx=5)
        def on_skill(skill):
            entries, events = self.game_logic.handle_combat_turn(skill, enemy)
            for entry in entries: log.insert(tk.END, entry + "\n"); log.see(tk.END)
            if "level_up" in events: messagebox.showinfo("Awans!", f"Osiągnięto poziom {self.game_logic.player.level}!")
            refresh()
        refresh()

def main():
    try:
        root = tk.Tk(); game = TriwersumGame(root); root.mainloop()
    except tk.TclError:
        print("Could not open display. This is expected in a headless environment.")

if __name__ == "__main__":
    main()
