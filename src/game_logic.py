import os
import json
import random
import tcod
from map_generator import MapGenerator, Tile, Door, Rect
from data_classes import Player, NPC, Enemy, Skill, Quest, Objective, Equipment, Item, Chest

SAVE_FILE = "savegame.json"

class Map:
    def __init__(self, width, height, tiles, doors, entities):
        self.width = width
        self.height = height
        self.tiles = tiles
        self.doors = doors
        self.entities = entities
        self.fov_map = self.initialize_fov()

    def initialize_fov(self):
        fov = tcod.map.Map(width=self.width, height=self.height, order="F")
        for y in range(self.height):
            for x in range(self.width):
                is_transparent = not self.tiles[x][y].block_sight
                is_walkable = not self.tiles[x][y].blocked

                door = self.get_door_at(x, y)
                if door and not door.is_open:
                    is_transparent = False
                    is_walkable = False

                fov.transparent[x, y] = is_transparent
                fov.walkable[x, y] = is_walkable
        return fov

    def compute_fov(self, x, y, radius):
        self.fov_map.compute_fov(x, y, radius, True, tcod.FOV_DIAMOND)

    def is_in_fov(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.fov_map.fov[x, y]
        return False

    def get_entity_at(self, x, y):
        for entity in self.entities:
            if entity.x == x and entity.y == y:
                return entity
        return None

    def get_door_at(self, x, y):
        for door in self.doors:
            if door.x == x and door.y == y:
                return door
        return None

    def to_dict(self):
        return {
            "width": self.width,
            "height": self.height,
            "tiles": [[tile.to_dict() for tile in col] for col in self.tiles],
            "doors": [door.to_dict() for door in self.doors],
            "entities": [entity.to_dict() for entity in self.entities if not isinstance(entity, Player)]
        }

    @classmethod
    def from_dict(cls, data, player, game_logic_helpers):
        width, height = data["width"], data["height"]
        tiles = [[Tile.from_dict(tile_data) for tile_data in col] for col in data["tiles"]]
        doors = [Door.from_dict(door_data) for door_data in data["doors"]]

        entities = [player]
        for e_data in data.get("entities", []):
            entities.append(game_logic_helpers.rebuild_entity(e_data))

        return cls(width, height, tiles, doors, entities)

class GameLogic:
    def __init__(self, grid_width=50, grid_height=35):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.map_generator = MapGenerator(grid_width, grid_height)
        self.player = None
        self.map = None
        self.initialize_game_state()

    def _define_content(self):
        self.master_skills = {
            "basic_attack": Skill("basic_attack", "Zwykły Atak", 0, 8, "Prosty atak fizyczny."),
            "harmonic_strike": Skill("harmonic_strike", "Harmoniczne Uderzenie", 10, 20, "Uderzenie nasycone Mocażem.", prerequisites=["basic_attack"]),
            "decay_pattern": Skill("decay_pattern", "Wzór Rozpadu", 25, 40, "Potężny, ale kosztowny atak.", prerequisites=["harmonic_strike"]),
            "fala_mocazu": Skill("fala_mocazu", "Fala Mocażu", 15, 5, "Obronne uderzenie, które leczy część obrażeń.", prerequisites=["basic_attack"]),
        }
        self.items = {
            "fartuch": Equipment("Fartuch Wuja", "Zwiększa maks. GD o 20.", "Ciało", bonuses={"gd_max": 20}),
            "kleszcze": Equipment("Kleszcze Króla Dzwonów", "Zwiększa maks. SM o 15.", "Ręka", bonuses={"sm_max": 15}),
        }
        self.static_npcs = [NPC(0, 0, "Mędrzec Ji-Ae", "ji_ae_start")]
        self.static_enemies_info = {
            "Wróg Funkcji": {"gd": 50, "skills": [self.master_skills["basic_attack"]], "xp": 40},
            "Siewca Paradygmatu": {"gd": 80, "skills": [self.master_skills["harmonic_strike"]], "xp": 100},
        }
        self.quests = {
            "main_quest": Quest("main_quest", "Echo Rozpadu", "Odnajdź źródło chaosu.", [Objective("Znajdź Mędrca Ji-Ae", "talk_to", "Mędrzec Ji-Ae")])
        }
        self.dialogues = {
            "ji_ae_start": {
                "text": "Witaj, wędrowcze. Czuję w tobie echo Mocażu. Czego szukasz w tych zapomnianych korytarzach?",
                "options": [{"label": "Kim jesteś?", "next": "ji_ae_who"}, {"label": "Szukam odpowiedzi.", "next": "ji_ae_answers"}]
            },
            "ji_ae_who": {"text": "Jestem tylko echem przeszłości, strażnikiem wiedzy, która umiera. Nazywają mnie Ji-Ae.", "options": [{"label": "Wróć", "next": "ji_ae_start"}]},
            "ji_ae_answers": {"text": "Odpowiedzi... one często prowadzą do kolejnych pytań. Jeśli chcesz je poznać, musisz być gotów na prawdę. Zacznij główny quest.", "options": [{"label": "Zgadzam się.", "next": "end", "action": "start_quest", "quest_key": "main_quest"}]}
        }

    def _place_entities(self):
        tiles, doors, rooms = self.map_generator.generate_bsp_map()
        entities = []

        player_x, player_y = rooms[0].center()
        self.player = Player(player_x, player_y)
        self.player.unlocked_skills.add("basic_attack")
        entities.append(self.player)

        spawn_points = []
        for room in rooms[1:]:
            spawn_points.append(room.center())
        random.shuffle(spawn_points)

        for npc_template in self.static_npcs:
            if spawn_points:
                x, y = spawn_points.pop()
                entities.append(NPC(x, y, npc_template.name, npc_template.dialogue_key))

        for name, info in self.static_enemies_info.items():
            if spawn_points:
                x, y = spawn_points.pop()
                entities.append(Enemy(x, y, name, info["gd"], info["skills"], info["xp"]))

        for i in range(3):
            if spawn_points:
                x, y = spawn_points.pop()
                entities.append(Chest(x, y, id=f"chest_{i}"))

        self.map = Map(self.grid_width, self.grid_height, tiles, doors, entities)

    def initialize_game_state(self, from_save=None):
        self._define_content()
        if from_save:
            self.load_from_state(from_save)
        else:
            self._place_entities()

    def get_save_state(self):
        return {"player": self.player.to_dict(), "map": self.map.to_dict()}

    def load_from_state(self, state):
        self.player = Player.from_dict(state["player"], self)
        self.map = Map.from_dict(state["map"], self.player, self)

    def handle_player_action(self, target_x, target_y):
        if not self.map.is_in_fov(target_x, target_y): return ("invalid_move", "Cannot see target.")

        door = self.map.get_door_at(target_x, target_y)
        if door and abs(target_x - self.player.x) <= 1 and abs(target_y - self.player.y) <= 1:
             door.is_open = not door.is_open
             self.map.initialize_fov()
             return ("interact_door", door)

        entity = self.map.get_entity_at(target_x, target_y)
        if entity:
            if isinstance(entity, NPC): return ("interact_npc", entity)
            if isinstance(entity, Enemy): return ("attack_enemy", entity)
            if isinstance(entity, Chest):
                if not entity.looted:
                    found_item = self.open_chest(entity)
                    return ("interact_chest", found_item)
                return ("info", "This chest is empty.")

        if self.map.fov_map.walkable[target_x, target_y] and abs(target_x - self.player.x) <= 1 and abs(target_y - self.player.y) <= 1:
             self.player.x, self.player.y = target_x, target_y
             return ("move", None)

        return ("invalid_move", None)

    def open_chest(self, chest):
        chest.looted = True
        found_item_key = random.choice(list(self.items.keys()))
        found_item = self.items[found_item_key]
        self.player.add_item(found_item)
        return found_item

    def handle_combat_turn(self, player_skill, enemy):
        log, events = [], set()
        p_dmg = player_skill.damage + self.player.get_stat_bonus("damage")
        enemy.gd -= p_dmg
        log.append(f"Zadałeś {p_dmg} obrażeń {enemy.name}.")
        if enemy.gd <= 0:
            log.append(f"{enemy.name} został pokonany!")
            self.player.gain_xp(enemy.xp_value)
            if self.player._level_up_core(): events.add("level_up")
            self.update_quest_progress("defeat", enemy.name)
            self.map.entities.remove(enemy)
            return log, events
        e_dmg = enemy.skills[0].damage
        self.player.gd -= e_dmg
        log.append(f"{enemy.name} zadał ci {e_dmg} obrażeń.")
        if self.player.gd <= 0: log.append("Zostałeś pokonany!")
        return log, events

    def start_quest(self, key):
        if key in self.quests and key not in self.player.quest_journal:
            self.player.quest_journal[key] = self.quests[key]
            self.player.quest_journal[key].status = "active"

    def update_quest_progress(self, event_type, target_name):
        for q in self.player.quest_journal.values():
            if q.status == "active": q.update_progress(event_type, target_name)

    def get_levelup_rewards(self):
        return [
            {"text": "+10 Maks. GD", "type": "gd_max", "tooltip": "Zwiększa maksymalną Gęstość Dopy."},
            {"text": "+5 Maks. SM", "type": "sm_max", "tooltip": "Zwiększa maksymalną Siłę Mocażu."},
            {"text": "+1 Punkt Umiejętności", "type": "skill_point", "tooltip": "Otrzymujesz punkt do wydania w drzewku umiejętności."}
        ]

    def apply_levelup_reward(self, reward_type):
        if reward_type == "skill_point": self.player.skill_points += 1
        else: setattr(self.player, reward_type, getattr(self.player, reward_type) + (10 if reward_type == "gd_max" else 5))
        self.player.reset_stats()

    def rebuild_item(self, item_data):
        if not item_data: return None
        return self.items.get(item_data["name"].lower().replace(" ", "_")) # Simple key from name

    def rebuild_entity(self, entity_data):
        class_name = entity_data["class"]
        if class_name == "NPC": return NPC.from_dict(entity_data)
        if class_name == "Chest": return Chest.from_dict(entity_data)
        if class_name == "Enemy":
            template = self.static_enemies_info[entity_data["name"]]
            return Enemy.from_dict(entity_data, template["skills"])
        return None

    def save_game(self, filepath=SAVE_FILE):
        with open(filepath, 'w') as f:
            json.dump(self.get_save_state(), f, indent=4)

    def load_game(self, filepath=SAVE_FILE):
        if not os.path.exists(filepath): return False
        with open(filepath, 'r') as f:
            state = json.load(f, object_hook=self.json_object_hook)
        self.initialize_game_state(from_save=state)
        return True

    def json_object_hook(self, d):
        if "class" in d:
            # This is where you would deserialize specific classes if needed,
            # but we handle it in from_dict methods.
            return d
        return d
