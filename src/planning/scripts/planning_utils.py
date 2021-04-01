#!/usr/bin/env python
from __future__ import division
import json
import random
import math
import numpy as np
import os.path
from itertools import product



# for test
# random.seed(19)
DRONE_MAX_SIDE = 0.15

def RRT(curr_x, curr_y, goal_x, goal_y, Map):
    """
    computes the RRT path
    :param curr_x:
    :param curr_y:
    :param goal_x:
    :param goal_y:
    :param Map:
    :return:
    """
    start_node = Node(curr_x, curr_y)
    goal_node = Node(goal_x, goal_y)
    Tree = [start_node]

    i = 0
    while True:
        rand_node = random_node(Map.airspace, goal_node)

        # closest node in tree
        nearest_node = find_nearest_node(Tree, rand_node)
        new_node = grow(rand_node, nearest_node, Map)

        if new_node != -1:
            Tree.append(new_node)

        if distance(Tree[-1], goal_node) <= 0.2:
            break
        i += 1
        
    path = generate_path(Tree[-1])

    return path

def generate_path(node):
    """
    generates the path
    :param node:
    :return:
    """
    path = [(node.x, node.y)]
    tmp = node
    parent = tmp.parent

    while parent is not None:
        path.insert(0, (parent.x, parent.y))
        tmp = parent
        parent = tmp.parent

    return path[1:]

def grow(rand_node, nearest_node, Map, steps = 1000):
    """
    check if I can grow the free is so returns the node to add to the tree
    :param rand_node:
    :param nearest_node: node that is in the tree already
    :param Map: map class to check if a path is allowable
    :param steps: how many steps it should take to check that there is no collision
    :return:
    """

    delta_x = (rand_node.x - nearest_node.x) / steps
    delta_y = (rand_node.y - nearest_node.y) / steps
    for i in range(1, steps +1):
        x = nearest_node.x + i * delta_x
        y = nearest_node.y + i * delta_y
        if not Map.is_passable(x, y):
            return -1
    rand_node.parent = nearest_node
    return rand_node

def distance(from_node, to_node):
    """
    Distance between 2 points in 2D space
    :param from_node: Node 1
    :param to_node: Node 2
    :return:
    """
    return math.hypot(from_node.x - to_node.x, from_node.y - to_node.y)

def find_nearest_node(tree, new_node):
    """
    Finds nearest nde
    :param tree:
    :param new_node:
    :return:
    """
    nearest = tree[0]
    dist = float('inf')

    for node in tree:
        new_dist = distance(node, new_node)
        if new_dist < dist:
            nearest = node
            dist = new_dist

    return nearest


def random_node(airspace, goal, prob_goal=0.2):
    """
    obtains a random node within the airspace
    :param airspace:
    :param goal:
    :param prob_goal:
    :return:
    """
    x_start, y_start, _, x_end, y_end, _ = airspace
    if random.uniform(0, 1) < prob_goal:
        return goal
    else:
        return Node(random.uniform(x_start, x_end), random.uniform(y_start, y_end))


class Node:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.parent = None
    def __str__(self):
        return "(x: {}, y:{})".format(self.x, self.y)



# The class representing the room and its limits
class Map:
    def __init__(self, map_path, expansion_factor=0.1):
        self.obstacles = []
        self.airspace = None
        self.mesh_grid = None
        self.occupancy_grid = None
        self.build_map(map_path, expansion_factor)

    def __str__(self):
        return "obstacles: {}\n airspace: {}".format(self.obstacles, self.airspace)

    def build_map(self, map_path, expansion_factor, discretization=0.05):
        """

        :param map_path:
        :return:
        """
        with open(map_path) as json_file:
            map_data = json.load(json_file)

        x_start, y_start, z_start = map_data["airspace"]["min"]
        x_end, y_end, z_end = map_data["airspace"]["max"]
        self.airspace = ((x_start, y_start, z_start, x_end, y_end, z_end))

        # check if obstacles exist
        if "walls" in map_data.keys():
            for obs in map_data["walls"]:
                x_start, y_start, z_start = obs["plane"]["start"]
                x_end, y_end, z_end = obs["plane"]["stop"]

                x_start = min(x_start, x_end)
                x_end = max(x_start, x_end)

                y_start = min(y_start, y_end)
                y_end = max(y_start, y_end)

                self.obstacles.append(( (x_start - DRONE_MAX_SIDE) - expansion_factor,
                                        (y_start - DRONE_MAX_SIDE) - expansion_factor,
                                       z_start,
                                        (x_end + DRONE_MAX_SIDE) + expansion_factor,
                                        (y_end + DRONE_MAX_SIDE) + expansion_factor,
                                       z_end))

        else:
            print("No obstacles")


        no_x = int(math.ceil((self.airspace[3] - self.airspace[0]) / discretization)) + 1
        no_y = int(math.ceil((self.airspace[4] - self.airspace[1]) / discretization)) + 1


        x_values = list(range(no_x))
        y_values = list(range(no_y))
        x_values = [i * discretization for i in x_values]
        y_values = [i * discretization for i in y_values]

        # self.free_space_grid = np.zeros(no_x, no_y)
        self.mesh_grid = [list(product([x_value], y_values)) for x_value in x_values]
        self.occupancy_grid = np.zeros((no_x, no_y))

        for i, row in enumerate(self.mesh_grid):
            for j, coords in enumerate(row):
                if not self.is_passable(coords[0], coords[1]):
                    self.occupancy_grid[i, j] = 1
        print()

    def is_passable(self, x, y):
        """
        checks if a
        """
        # check if it is within the airspace
        if x + DRONE_MAX_SIDE > self.airspace[3] or x - DRONE_MAX_SIDE < self.airspace[0]   or y + DRONE_MAX_SIDE > self.airspace[4] or y - DRONE_MAX_SIDE < self.airspace[1]:
            return False
        # check against obstacles
        for obs in self.obstacles:
            x_start, y_start, _, x_end, y_end, _ = obs
            if max(x_start, x_end) >=  x >= min(x_start, x_end) and max(y_start, y_end) >=  y >= min(y_start, y_end):
                return False
        return True


def test():
    # world_map = Map("course_packages/dd2419_resources/worlds_json/planning_test_map.json")
    my_path = os.path.abspath(os.path.dirname(__file__))
    file = "lucas_room_screen.world.json"
    map_path = os.path.join(my_path, "../..", "course_packages/dd2419_resources/worlds_json", file)
    world_map = Map(map_path)
    print(world_map)
    # world_map = Map("src/course_packages/dd2419_resources/worlds_json/tutorial_1.world.json")
    result = RRT(0.5, 0.8, 1.6, 1, world_map)
    print(result)
if __name__ == "__main__":
    test()
