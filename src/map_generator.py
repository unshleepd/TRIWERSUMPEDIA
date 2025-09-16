import random

class MapGenerator:
    """
    Generates a 2D map using a Cellular Automata algorithm.
    1 represents a wall, 0 represents a floor.
    """
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.map = [[0 for _ in range(self.height)] for _ in range(self.width)]

    def generate_map(self, wall_probability=0.45, iterations=4, wall_rule=4, floor_rule=5):
        """
        Generates and returns a new map.
        """
        self._random_fill(wall_probability)
        for _ in range(iterations):
            self._smooth_map(wall_rule, floor_rule)
        return self.map

    def _random_fill(self, probability):
        """Fills the map with a random pattern of walls and floors."""
        for x in range(self.width):
            for y in range(self.height):
                if x == 0 or x == self.width - 1 or y == 0 or y == self.height - 1:
                    self.map[x][y] = 1  # Create a border of walls
                else:
                    self.map[x][y] = 1 if random.random() < probability else 0

    def _smooth_map(self, wall_rule, floor_rule):
        """Runs one iteration of the Cellular Automata simulation."""
        new_map = [row[:] for row in self.map] # Create a deep copy
        for x in range(1, self.width - 1):
            for y in range(1, self.height - 1):
                wall_neighbors = self._get_wall_neighbors(x, y)

                if self.map[x][y] == 1:
                    if wall_neighbors < wall_rule: new_map[x][y] = 0
                else:
                    if wall_neighbors >= floor_rule: new_map[x][y] = 1
        self.map = new_map

    def _get_wall_neighbors(self, x, y):
        """Counts the number of wall tiles in the 8 surrounding neighbors."""
        count = 0
        for i in range(x - 1, x + 2):
            for j in range(y - 1, y + 2):
                if i == x and j == y: continue
                if 0 <= i < self.width and 0 <= j < self.height:
                    count += self.map[i][j]
                else:
                    count += 1
        return count

    def find_regions(self, tile_type=0):
        """
        Finds all contiguous regions of a given tile type using flood fill.
        Returns a list of regions, where each region is a list of (x, y) tuples.
        """
        regions = []
        visited = set()

        for x in range(self.width):
            for y in range(self.height):
                if (x, y) not in visited and self.map[x][y] == tile_type:
                    new_region = []
                    stack = [(x, y)]
                    visited.add((x, y))

                    while stack:
                        px, py = stack.pop()
                        new_region.append((px, py))

                        # Check 4 cardinal directions
                        for i, j in [(px, py + 1), (px, py - 1), (px + 1, py), (px - 1, py)]:
                            if 0 <= i < self.width and 0 <= j < self.height:
                                if (i, j) not in visited and self.map[i][j] == tile_type:
                                    visited.add((i, j))
                                    stack.append((i, j))
                    regions.append(new_region)
        return regions
