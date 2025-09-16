class Skill:
    def __init__(self, name, cost, damage, description=""):
        self.name, self.cost, self.damage, self.description = name, cost, damage, description

class Objective:
    def __init__(self, description, target_type, target_name):
        self.description = description
        self.target_type = target_type
        self.target_name = target_name
        self.is_done = False
    def to_dict(self):
        return self.is_done
    @classmethod
    def from_dict(cls, data, description, target_type, target_name):
        obj = cls(description, target_type, target_name)
        obj.is_done = data
        return obj

class Quest:
    def __init__(self, key, title, description, objectives, reward=None):
        self.key, self.title, self.description, self.objectives, self.reward, self.status = key, title, description, objectives, reward, "inactive"
    def to_dict(self):
        return {"status": self.status, "objectives": [obj.to_dict() for obj in self.objectives]}
    @classmethod
    def from_dict(cls, data, key, title, description, objectives, reward=None):
        quest = cls(key, title, description, [Objective.from_dict(d, o.description, o.target_type, o.target_name) for d, o in zip(data["objectives"], objectives)], reward)
        quest.status = data["status"]
        return quest

class Item:
    def __init__(self, name, description, item_type="misc"):
        self.name, self.description, self.item_type = name, description, item_type
    def to_dict(self):
        return {"name": self.name, "type": self.item_type}

class Equipment(Item):
    def __init__(self, name, description, slot, bonuses=None):
        super().__init__(name, description, item_type="equipment")
        self.slot = slot
        self.bonuses = bonuses if bonuses else {}
    def to_dict(self):
        data = super().to_dict()
        data.update({"slot": self.slot, "bonuses": self.bonuses})
        return data

class Player:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.gd_max, self.gd, self.sm_max, self.sm, self.wgk = 100, 100, 50, 50, 0
        self.level, self.xp, self.xp_to_next_level = 1, 0, 100
        self.base_damage = 5
        self.damage_bonus = 0
        self.inventory = [Equipment("Fartuch Wuja", "Zwiększa maks. GD o 20.", "Ciało", bonuses={"gd_max": 20})]
        self.equipment = {"Ręka": None, "Ciało": None}
        self.quest_journal = {}
        self.skills = [Skill("Zwykły Atak", 0, 8, "Prosty atak fizyczny."), Skill("Harmoniczne Uderzenie", 10, 20, "Uderzenie nasycone Mocażem.")]
        self.icon = "@"
        self.color = "lightblue"
        self.name = "Gracz"

    def to_dict(self):
        return {
            "x": self.x, "y": self.y, "gd_max": self.gd_max, "gd": self.gd, "sm_max": self.sm_max, "sm": self.sm, "level": self.level, "xp": self.xp, "xp_to_next_level": self.xp_to_next_level,
            "inventory": [item.to_dict() for item in self.inventory],
            "equipment": {slot: item.to_dict() if item else None for slot, item in self.equipment.items()},
            "quest_journal": {key: quest.to_dict() for key, quest in self.quest_journal.items()}
        }

    def get_total_damage(self, skill_damage):
        return skill_damage + self.damage_bonus

    def _level_up_core(self):
        if self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
            return True
        return False

    def add_xp(self, amount):
        self.xp += amount
        leveled_up = False
        while self.xp >= self.xp_to_next_level:
            self._level_up_core()
            leveled_up = True
        return leveled_up

    def add_quest(self, quest):
        if quest.key not in self.quest_journal:
            quest.status = "active"
            self.quest_journal[quest.key] = quest

    def add_item(self, item):
        self.inventory.append(item)

    def equip(self, item):
        if item.item_type == "equipment" and item in self.inventory:
            if self.equipment.get(item.slot):
                self.unequip(self.equipment[item.slot])
            self.inventory.remove(item)
            self.equipment[item.slot] = item
            for stat, value in item.bonuses.items():
                setattr(self, stat, getattr(self, stat) + value)
            self.gd = min(self.gd, self.gd_max)
            return True
        return False

    def unequip(self, item):
        if item.item_type == "equipment" and item == self.equipment.get(item.slot):
            self.equipment[item.slot] = None
            self.inventory.append(item)
            for stat, value in item.bonuses.items():
                setattr(self, stat, getattr(self, stat) - value)
            self.gd = min(self.gd, self.gd_max)
            return True
        return False

class NPC:
    def __init__(self, x, y, name, dialogue_key):
        self.x, self.y, self.name, self.dialogue_key = x, y, name, dialogue_key
        self.icon = "N"
        self.color = "lightgreen"

class Enemy:
    def __init__(self, x, y, name, gd, skills, xp_reward):
        self.x, self.y, self.name, self.gd, self.skills, self.xp_reward = x, y, name, gd, skills, xp_reward
        self.icon = "E"
        self.color = "#E06666"

    def to_dict(self):
        return {"name": self.name, "x": self.x, "y": self.y, "gd": self.gd}
