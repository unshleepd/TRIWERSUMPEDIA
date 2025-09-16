import os
import json
import random
from map_generator import MapGenerator
from data_classes import Player, NPC, Enemy, Skill, Quest, Objective, Equipment, Item

SAVE_FILE = "savegame.json"

class GameLogic:
    def __init__(self, grid_width, grid_height):
        self.grid_width, self.grid_height = grid_width, grid_height
        self.map_layout = []
        self.map_generator = MapGenerator(grid_width, grid_height)
        self.player = None
        self.initialize_game_state()

    def _define_content(self):
        self.master_skills = {
            "basic_attack": Skill("basic_attack", "Zwykły Atak", 0, 8, "Prosty atak fizyczny."),
            "harmonic_strike": Skill("harmonic_strike", "Harmoniczne Uderzenie", 10, 20, "Uderzenie nasycone Mocażem.", prerequisites=["basic_attack"]),
            "decay_pattern": Skill("decay_pattern", "Wzór Rozpadu", 25, 40, "Potężny, ale kosztowny atak.", prerequisites=["harmonic_strike"]),
            "fala_mocazu": Skill("fala_mocazu", "Fala Mocażu", 15, 5, "Obronne uderzenie, które leczy część obrażeń.", prerequisites=["basic_attack"]),
            "aegis_of_kopec": Skill("aegis_of_kopec", "Egida Kopcia", 20, 0, "Tworzy barierę ochronną.", prerequisites=["fala_mocazu"]),
            "cieniste_ostrze": Skill("cieniste_ostrze", "Cieniste Ostrze", 0, 18, "Potężny atak cienia."),
            "cios_paradygmatu": Skill("cios_paradygmatu", "Cios Paradygmatu", 0, 12, "Atak zmieniający rzeczywistość."),
            "cios_funkcyjny": Skill("cios_funkcyjny", "Cios Funkcyjny", 0, 8, "Atak zakłócający harmonię.")
        }
        self.items = {"fartuch": Equipment("Fartuch Wuja", "Zwiększa maks. GD o 20.", "Ciało", bonuses={"gd_max": 20}), "kleszcze": Equipment("Kleszcze Króla Dzwonów", "Zwiększa maks. SM o 15.", "Ręka", bonuses={"sm_max": 15}), "synonim": Equipment("Synonim Grzechu", "Potężny artefakt. +15 do obrażeń, +5 do WGK.", "Ręka", bonuses={"damage_bonus": 15, "wgk": 5})}
        self.static_npcs = [NPC(0, 0, "Mędrzec Ji-Ae", "ji_ae_start"), NPC(0, 0, "Lord Bonglord", "bonglord_start")]
        self.static_enemies = {
            "Wróg Funkcji": (50, [self.master_skills["cios_funkcyjny"]], 40),
            "Siewca Paradygmatu": (80, [self.master_skills["cios_paradygmatu"]], 100),
            "Cień Szkarłatnego Pana": (120, [self.master_skills["cieniste_ostrze"]], 150),
            "Heretyk Krwawego Słońca": (60, [self.master_skills["decay_pattern"]], 120)
        }
        self.quests = {"bonglord_quest": Quest("bonglord_quest", "Próba Harmonii", "Pomóż Lordowi Bonglordowi.", [Objective("Porozmawiaj z Mędrcem Ji-Ae", "talk_to", "Mędrzec Ji-Ae"), Objective("Pokonaj Siewcę Paradygmatu", "defeat", "Siewca Paradygmatu")], reward={"type": "item", "key": "kleszcze"}), "shadow_quest": Quest("shadow_quest", "Zagrożenie z Cienia", "Pokonaj Cień Szkarłatnego Pana.", [Objective("Pokonaj Cień Szkarłatnego Pana", "defeat", "Cień Szkarłatnego Pana")], reward={"type": "item", "key": "synonim"})}

    def _place_entities(self):
        floor_regions = self.map_generator.find_regions(tile_type=0)
        if not floor_regions: self.initialize_game_state(); return
        largest_region = max(floor_regions, key=len)

        enemies_to_spawn = dict(self.static_enemies)
        if self.player:
            bonglord_quest = self.player.quest_journal.get("bonglord_quest")
            if not (bonglord_quest and bonglord_quest.status == "rewarded"):
                if "Cień Szkarłatnego Pana" in enemies_to_spawn: del enemies_to_spawn["Cień Szkarłatnego Pana"]
        elif "Cień Szkarłatnego Pana" in enemies_to_spawn:
            del enemies_to_spawn["Cień Szkarłatnego Pana"]

        entity_count = 1 + len(self.static_npcs) + len(enemies_to_spawn)
        if len(largest_region) < entity_count: self.initialize_game_state(); return

        spawn_points = random.sample(largest_region, entity_count)
        player_pos = spawn_points.pop()
        if not self.player: self.player = Player(player_pos[0], player_pos[1])
        else: self.player.x, self.player.y = player_pos

        self.npcs = []
        for npc_template in self.static_npcs:
            pos = spawn_points.pop(); self.npcs.append(NPC(pos[0], pos[1], npc_template.name, npc_template.dialogue_key))

        self.enemies = []
        for name, (gd, skills, xp) in enemies_to_spawn.items():
            pos = spawn_points.pop(); self.enemies.append(Enemy(pos[0], pos[1], name, gd, skills, xp))

    def initialize_game_state(self, from_save=None):
        self._define_content()
        if from_save: self.load_from_state(from_save)
        else:
            self.player = None
            self.map_layout = self.map_generator.generate_map()
            self._place_entities()
        self.dialogues = self.get_dialogues()

    def get_levelup_rewards(self):
        return [
            {"type": "gd", "text": "+20 Maks. GD", "tooltip": "Zwiększa maksymalną Gęstość Dopy i w pełni leczy."},
            {"type": "sm", "text": "+10 Maks. SM", "tooltip": "Zwiększa maksymalny Strumień Mocażu i w pełni go odnawia."},
            {"type": "skill_point", "text": "+1 Pkt. Umiejętności", "tooltip": "Otrzymaj punkt do wydania w Drzewku Umiejętności."}
        ]

    def apply_levelup_reward(self, reward_type):
        if reward_type == "gd": self.player.gd_max += 20; self.player.gd = self.player.gd_max
        elif reward_type == "sm": self.player.sm_max += 10; self.player.sm = self.player.sm_max
        elif reward_type == "skill_point": self.player.skill_points += 1

    def get_save_state(self):
        return {"player": self.player.to_dict(), "enemies": [e.to_dict() for e in self.enemies], "map_layout": self.map_layout}

    def load_from_state(self, state):
        self.map_layout = state["map_layout"]
        p_data = state["player"]
        self.player = Player(p_data["x"], p_data["y"])
        for key in ["gd_max", "gd", "sm_max", "sm", "level", "xp", "xp_to_next_level", "skill_points"]:
            if key in p_data: setattr(self.player, key, p_data[key])
        self.player.unlocked_skills = set(p_data.get("unlocked_skills", {"basic_attack"}))
        self.player.inventory = [self.rebuild_item(item_data) for item_data in p_data.get("inventory", [])]
        self.player.equipment = {slot: self.rebuild_item(item_data) for slot, item_data in p_data.get("equipment", {}).items()}
        for item in self.player.equipment.values():
            if item and item.item_type == "equipment":
                for stat, value in item.bonuses.items(): setattr(self.player, stat, getattr(self.player, stat) + value)

        self.player.quest_journal = {}
        for key, q_data in p_data.get("quest_journal", {}).items():
            template = self.quests[key]
            # Correctly reconstruct the quest without using __dict__
            self.player.quest_journal[key] = Quest.from_dict(
                q_data,
                key=template.key,
                title=template.title,
                description=template.description,
                objectives=template.objectives,
                reward=template.reward
            )

        self.enemies = []
        for e_data in state["enemies"]:
            name, gd, skills, xp = e_data["name"], e_data["gd"], self.static_enemies[e_data["name"]][1], self.static_enemies[e_data["name"]][2]
            self.enemies.append(Enemy(e_data["x"], e_data["y"], name, gd, skills, xp))

    def rebuild_item(self, item_data):
        if not item_data: return None
        for item in self.items.values():
            if item.name == item_data["name"]: return Equipment(item.name, item.description, item.slot, item.bonuses)
        return Item(item_data.get("name", "Unknown"), "Unknown")

    def save_game(self):
        with open(SAVE_FILE, 'w') as f: json.dump(self.get_save_state(), f, indent=4)

    def load_game(self):
        if not os.path.exists(SAVE_FILE): return False
        with open(SAVE_FILE, 'r') as f: state = json.load(f)
        self.initialize_game_state(from_save=state)
        return True

    def get_entity_at(self, x, y):
        for entity in self.npcs + self.enemies:
            if entity.x == x and entity.y == y: return entity
        return None

    def move_player_or_interact(self, target_x, target_y):
        if not (0 <= target_x < self.grid_width and 0 <= target_y < self.grid_height): return ("invalid", None)
        if self.map_layout[target_x][target_y] == 1: return ("invalid", None)
        entity = self.get_entity_at(target_x, target_y)
        if entity:
            if isinstance(entity, NPC): return ("interact", entity)
            if isinstance(entity, Enemy): return ("combat", entity)
        if abs(target_x - self.player.x) + abs(target_y - self.player.y) == 1:
            self.player.x, self.player.y = target_x, target_y
            return ("move", None)
        return ("invalid", None)

    def handle_combat_turn(self, player_skill, enemy):
        log, events = [], []
        if self.player.sm < player_skill.cost: log.append("Brak Strumienia Mocażu!"); return log, events
        total_player_damage = self.player.get_total_damage(player_skill.damage)
        enemy.gd -= total_player_damage
        log.append(f"Używasz '{player_skill.name}' i zadajesz {total_player_damage} obrażeń.")
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
        dialogues = {"ji_ae_start": {"text": "Witaj, wędrowcze.", "options": []}, "ji_ae_quest_talk": {"text": "Ach, więc to o to chodzi. Siewca Paradygmatu na północy... Jest potężny. Uważaj.", "options": [{"label": "[Dziękuję za ostrzeżenie]", "next": "end", "action": "update_quest", "target": "Mędrzec Ji-Ae"}]}, "bonglord_reward": {"text": "Wykonałeś zadanie. Równowaga wraca. Przyjmij ten dar.", "options": [{"label": "[Weź nagrodę]", "next": "end", "action": "grant_reward", "quest_key": "bonglord_quest"}]}, "shadow_quest_offer": {"text": "Czuję nowe zakłócenie... mroczniejsze. Cień z przeszłości. Znajdź go i zniszcz.", "options": [{"label": "Uczynię to.", "next": "end", "action": "start_quest", "quest_key": "shadow_quest"}, {"label": "To zbyt niebezpieczne.", "next": "end"}]}, "shadow_quest_reward": {"text": "Cień zniknął. Twoja odwaga jest wielka. Ale strzeż się mocy, którą zdobyłeś.", "options": [{"label": "[Weź Synonim Grzechu]", "next": "end", "action": "grant_reward", "quest_key": "shadow_quest"}]}}
        if self.player:
            ji_ae_quest = self.player.quest_journal.get("bonglord_quest")
            if ji_ae_quest and ji_ae_quest.status == "active":
                dialogues["ji_ae_start"]["options"].append({"label": "Lord Bonglord mnie przysyła.", "next": "ji_ae_quest_talk"})
        dialogues["ji_ae_start"]["options"].append({"label": "[Odejdź]", "next": "end"})
        bonglord_start_node = {"text": "Czuję harmonię w twoim oddechu...", "options": []}
        if self.player:
            shadow_quest = self.player.quest_journal.get("shadow_quest")
            bonglord_quest = self.player.quest_journal.get("bonglord_quest")
            if shadow_quest and shadow_quest.status == 'completed':
                 bonglord_start_node["options"].append({"label": "[Podziękuj za radę]", "next": "end"})
            elif shadow_quest: pass
            elif bonglord_quest and bonglord_quest.status == 'rewarded':
                bonglord_start_node["options"].append({"label": "Pojawiło się nowe zagrożenie?", "next": "shadow_quest_offer"})
            if bonglord_quest and bonglord_quest.status == 'completed':
                bonglord_start_node["options"].append({"label": "Wróciłem, mistrzu.", "next": "bonglord_reward"})
            if not bonglord_quest:
                bonglord_start_node["options"].append({"label": "Coś zakłóca przepływy?", "next": "bonglord_quest_offer"})
        bonglord_start_node["options"].append({"label": "[Odejdź]", "next": "end"})
        dialogues["bonglord_start"] = bonglord_start_node
        return dialogues
