class Entity:
    def __init__(self, x, y, name, icon, color):
        self.x, self.y, self.name, self.icon, self.color = x, y, name, icon, color

    def to_dict(self):
        return {
            "class": self.__class__.__name__, "x": self.x, "y": self.y, "name": self.name,
            "icon": self.icon, "color": self.color
        }

class Skill:
    def __init__(self, key, name, cost, damage, description="", prerequisites=None):
        self.key, self.name, self.cost, self.damage, self.description, self.prerequisites = key, name, cost, damage, description, prerequisites or []

class Objective:
    def __init__(self, description, target_type, target_name):
        self.description, self.target_type, self.target_name, self.is_done = description, target_type, target_name, False
    def to_dict(self): return self.is_done
    @classmethod
    def from_dict(cls, data, description, target_type, target_name):
        obj = cls(description, target_type, target_name); obj.is_done = data; return obj

class Quest:
    def __init__(self, key, title, description, objectives, reward=None):
        self.key, self.title, self.description, self.objectives, self.reward, self.status = key, title, description, objectives, reward, "inactive"
    def to_dict(self): return {"status": self.status, "objectives": [obj.to_dict() for obj in self.objectives]}
    @classmethod
    def from_dict(cls, data, quest_template):
        objectives = [Objective.from_dict(d, o.description, o.target_type, o.target_name) for d, o in zip(data["objectives"], quest_template.objectives)]
        quest = cls(quest_template.key, quest_template.title, quest_template.description, objectives, quest_template.reward); quest.status = data["status"]; return quest
    def update_progress(self, event_type, target_name):
        for obj in self.objectives:
            if not obj.is_done and obj.target_type == event_type and obj.target_name == target_name:
                obj.is_done = True

class Item:
    def __init__(self, name, description, item_type="misc"): self.name, self.description, self.item_type = name, description, item_type
    def to_dict(self): return {"name": self.name, "item_type": self.item_type, "class": self.__class__.__name__}

class Equipment(Item):
    def __init__(self, name, description, slot, bonuses=None):
        super().__init__(name, description, item_type="equipment"); self.slot, self.bonuses = slot, bonuses or {}
    def to_dict(self):
        data = super().to_dict(); data.update({"slot": self.slot, "bonuses": self.bonuses}); return data

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, "Gracz", "@", "lightblue")
        self.gd_max, self.gd, self.sm_max, self.sm, self.wgk = 100, 100, 50, 50, 0
        self.level, self.xp, self.xp_to_next_level = 1, 0, 100
        self.skill_points = 1
        self.unlocked_skills = {"basic_attack"}
        self.inventory = []
        self.equipment = {"Ręka": None, "Ciało": None}
        self.quest_journal = {}

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "gd_max": self.gd_max, "gd": self.gd, "sm_max": self.sm_max, "sm": self.sm, "wgk": self.wgk,
            "level": self.level, "xp": self.xp, "xp_to_next_level": self.xp_to_next_level,
            "skill_points": self.skill_points, "unlocked_skills": list(self.unlocked_skills),
            "inventory": [item.to_dict() for item in self.inventory],
            "equipment": {slot: item.to_dict() if item else None for slot, item in self.equipment.items()},
            "quest_journal": {key: quest.to_dict() for key, quest in self.quest_journal.items()}
        })
        return data

    @classmethod
    def from_dict(cls, data, game_logic):
        player = cls(data["x"], data["y"])
        for key in ["gd_max", "gd", "sm_max", "sm", "wgk", "level", "xp", "xp_to_next_level", "skill_points"]:
            if key in data: setattr(player, key, data[key])
        player.unlocked_skills = set(data.get("unlocked_skills", {"basic_attack"}))
        player.inventory = [game_logic.rebuild_item(item_data) for item_data in data.get("inventory", [])]
        player.equipment = {slot: game_logic.rebuild_item(item_data) for slot, item_data in data.get("equipment", {}).items() if item_data}
        for key, q_data in data.get("quest_journal", {}).items():
            player.quest_journal[key] = Quest.from_dict(q_data, game_logic.quests[key])
        return player

    def gain_xp(self, amount):
        self.xp += amount
        leveled_up = False
        while self._level_up_core():
            leveled_up = True
        return leveled_up

    def _level_up_core(self):
        if self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level; self.level += 1
            self.xp_to_next_level = int(self.xp_to_next_level * 1.5); self.skill_points += 1
            self.reset_stats()
            return True
        return False

    def reset_stats(self):
        self.gd = self.gd_max
        self.sm = self.sm_max

    def add_item(self, item): self.inventory.append(item)
    def can_unlock_skill(self, skill): return self.skill_points > 0 and all(prereq in self.unlocked_skills for prereq in skill.prerequisites)
    def unlock_skill(self, skill_key, master_skill_list):
        skill = master_skill_list.get(skill_key)
        if skill and skill_key not in self.unlocked_skills and self.can_unlock_skill(skill):
            self.skill_points -= 1; self.unlocked_skills.add(skill_key); return True
        return False
    def get_stat_bonus(self, stat):
        bonus = 0
        for item in self.equipment.values():
            if item: bonus += item.bonuses.get(stat, 0)
        return bonus

    def equip(self, item):
        if item.item_type == "equipment" and item in self.inventory:
            if self.equipment.get(item.slot):
                self.unequip(self.equipment[item.slot])
            self.inventory.remove(item)
            self.equipment[item.slot] = item
            for stat, value in item.bonuses.items():
                setattr(self, stat, getattr(self, stat) + value)
            self.reset_stats()
            return True
        return False

    def unequip(self, item):
        if item.item_type == "equipment" and item in self.equipment.values() and self.equipment[item.slot] == item:
            self.equipment[item.slot] = None
            self.inventory.append(item)
            for stat, value in item.bonuses.items():
                setattr(self, stat, getattr(self, stat) - value)
            self.reset_stats()
            return True
        return False

class NPC(Entity):
    def __init__(self, x, y, name, dialogue_key):
        super().__init__(x, y, name, "N", "lightgreen")
        self.dialogue_key = dialogue_key
    def to_dict(self):
        data = super().to_dict(); data["dialogue_key"] = self.dialogue_key; return data
    @classmethod
    def from_dict(cls, data):
        return cls(data["x"], data["y"], data["name"], data["dialogue_key"])

class Enemy(Entity):
    def __init__(self, x, y, name, gd, skills, xp_value):
        super().__init__(x, y, name, "E", "#E06666")
        self.gd, self.skills, self.xp_value = gd, skills, xp_value
    def to_dict(self):
        data = super().to_dict(); data.update({"gd": self.gd, "xp_value": self.xp_value}); return data
    @classmethod
    def from_dict(cls, data, skills):
        return cls(data["x"], data["y"], data["name"], data["gd"], skills, data["xp_value"])

class Chest(Entity):
    def __init__(self, x, y, id):
        super().__init__(x, y, "Skrzynia", "*", "yellow")
        self.id = id; self.looted = False
    def to_dict(self):
        data = super().to_dict(); data.update({"id": self.id, "looted": self.looted}); return data
    @classmethod
    def from_dict(cls, data):
        chest = cls(data["x"], data["y"], data["id"]); chest.looted = data["looted"]; return chest
