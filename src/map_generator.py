import random

class Tile:
    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked
        if block_sight is None:
            block_sight = blocked
        self.block_sight = block_sight
        self.explored = False

    def to_dict(self):
        return {"blocked": self.blocked, "block_sight": self.block_sight, "explored": self.explored}

    @classmethod
    def from_dict(cls, data):
        tile = cls(data["blocked"], data["block_sight"])
        tile.explored = data.get("explored", False)
        return tile

class Door:
    def __init__(self, x, y, is_open=False):
        self.x = x
        self.y = y
        self.is_open = is_open
        self.icon = "+" if is_open else "D"
        self.color = "yellow"

    def to_dict(self):
        return {"x": self.x, "y": self.y, "is_open": self.is_open}

    @classmethod
    def from_dict(cls, data):
        return cls(data["x"], data["y"], data["is_open"])

class Rect:
    def __init__(self, x, y, w, h):
        self.x1, self.y1 = x, y
        self.x2, self.y2 = x + w, y + h
    def center(self):
        return (self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2
    def intersects(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

class MapGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = None
        self.rooms = []
        self.doors = []

    def generate_bsp_map(self, min_room_size=5):
        self.tiles = [[Tile(True) for _ in range(self.height)] for _ in range(self.width)]
        self.rooms = []
        self.doors = []

        root_partition = Rect(1, 1, self.width - 2, self.height - 2)
        self._recursive_split(root_partition, 4, min_room_size)

        for i in range(len(self.rooms) - 1):
            self._create_corridor(self.rooms[i].center(), self.rooms[i+1].center())

        return self.tiles, self.doors, self.rooms

    def _recursive_split(self, partition, iterations, min_room_size):
        if iterations == 0:
            self._create_room_in_partition(partition, min_room_size)
            return

        split_horizontally = random.choice([True, False])

        min_partition_size = min_room_size + 2
        if partition.x2 - partition.x1 < min_partition_size * 2:
            split_horizontally = False
        if partition.y2 - partition.y1 < min_partition_size * 2:
            split_horizontally = True

        can_split_h = (partition.x2 - partition.x1) >= min_partition_size * 2
        can_split_v = (partition.y2 - partition.y1) >= min_partition_size * 2

        if not can_split_h and not can_split_v:
            self._create_room_in_partition(partition, min_room_size)
            return

        if split_horizontally and can_split_h:
            split = random.randint(partition.x1 + min_partition_size, partition.x2 - min_partition_size)
            self._recursive_split(Rect(partition.x1, partition.y1, split - partition.x1, partition.y2 - partition.y1), iterations - 1, min_room_size)
            self._recursive_split(Rect(split, partition.y1, partition.x2 - split, partition.y2 - partition.y1), iterations - 1, min_room_size)
        elif can_split_v:
            split = random.randint(partition.y1 + min_partition_size, partition.y2 - min_partition_size)
            self._recursive_split(Rect(partition.x1, partition.y1, partition.x2 - partition.x1, split - partition.y1), iterations - 1, min_room_size)
            self._recursive_split(Rect(partition.x1, split, partition.x2 - partition.x1, partition.y2 - split), iterations - 1, min_room_size)
        else:
            self._create_room_in_partition(partition, min_room_size)

    def _create_room_in_partition(self, partition, min_room_size):
        part_w = partition.x2 - partition.x1
        part_h = partition.y2 - partition.y1

        max_room_w = part_w - 2
        max_room_h = part_h - 2

        if max_room_w < min_room_size or max_room_h < min_room_size:
            return

        room_w = random.randint(min_room_size, max_room_w)
        room_h = random.randint(min_room_size, max_room_h)

        room_x = random.randint(partition.x1 + 1, partition.x2 - room_w - 1)
        room_y = random.randint(partition.y1 + 1, partition.y2 - room_h - 1)

        new_room = Rect(room_x, room_y, room_w, room_h)
        self.rooms.append(new_room)
        for x in range(new_room.x1, new_room.x2):
            for y in range(new_room.y1, new_room.y2):
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.tiles[x][y].blocked = False
                    self.tiles[x][y].block_sight = False

    def _create_corridor(self, start, end):
        x1, y1 = start; x2, y2 = end
        if random.random() < 0.5:
            self._create_h_tunnel(x1, x2, y1); self._create_v_tunnel(y1, y2, x2)
        else:
            self._create_v_tunnel(y1, y2, x1); self._create_h_tunnel(x1, x2, y2)

    def _create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                if self.tiles[x][y].blocked:
                    is_door = True
                    for door in self.doors:
                        if door.x == x and door.y == y:
                            is_door = False
                            break
                    if is_door:
                        self.doors.append(Door(x, y))
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False

    def _create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
             if 0 <= x < self.width and 0 <= y < self.height:
                if self.tiles[x][y].blocked:
                    is_door = True
                    for door in self.doors:
                        if door.x == x and door.y == y:
                            is_door = False
                            break
                    if is_door:
                        self.doors.append(Door(x, y))
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False

    def find_regions(self, tile_type=0):
        # This method is now somewhat obsolete as we work with Tile objects,
        # but can be kept for debugging or adapted if needed.
        regions = []; visited = set()
        for x in range(self.width):
            for y in range(self.height):
                tile_is_type = (not self.tiles[x][y].blocked) if tile_type == 0 else self.tiles[x][y].blocked
                if (x, y) not in visited and tile_is_type:
                    new_region = []; stack = [(x, y)]; visited.add((x, y))
                    while stack:
                        px, py = stack.pop(); new_region.append((px, py))
                        for i, j in [(px, py + 1), (px, py - 1), (px + 1, py), (px - 1, py)]:
                            if 0 <= i < self.width and 0 <= j < self.height:
                                tile_is_type_neighbor = (not self.tiles[i][j].blocked) if tile_type == 0 else self.tiles[i][j].blocked
                                if (i, j) not in visited and tile_is_type_neighbor:
                                    visited.add((i, j)); stack.append((i, j))
                    regions.append(new_region)
        return regions
