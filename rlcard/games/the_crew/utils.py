import os
import json
import random

import numpy as np
from collections import OrderedDict

import rlcard

from rlcard.games.the_crew.card import Card

class Mission:
    numTaskCards = 0
    taskCards = []
    taskTokens = []
    numAttempts = 0

    def __init__(self, numTaskCards, taskTokens):
        self.numAttempts = 0
        self.numTaskCards = numTaskCards
        self.taskTokens = taskTokens



# a map of abstract action to its index and a list of abstract action
with open(os.path.join('rlcard/games/the_crew/jsondata/action_space.json'), 'r') as file:
    ACTION_SPACE = json.load(file, object_pairs_hook=OrderedDict)
    ACTION_LIST = list(ACTION_SPACE.keys())

# a map of color to its index
COLOR_MAP = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4}

# a map of trait to its index
TRAIT_MAP = {'0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7,
             '8': 8, '9': 9}


def init_deck():
    deck = []
    for i in range(0, 10):
        for j in range(4):
            deck.append(Card(i, j, False))
    return deck

def init_task():
    task = []
    tasking = []
    for i in range(0, 9):
        for j in range(4):
            task.append(Card(i, j, True))
    random.shuffle(task)
    # for i in range(4):
    #     card = task.pop()
    #     tasking.append(card.setToken(i))
    return task


def cards2list(cards):
    ''' Get the corresponding string representation of cards

    Args:
        cards (list): list of UnoCards objects

    Returns:
        (string): string representation of cards
    '''
    cards_list = []
    for card in cards:
        cards_list.append(card.get_str())
    return cards_list

def encode_hand(plane, hand):
    ''' Encode hand and represerve it into plane

    Args:
        plane (array): 3*4*15 numpy array
        hand (list): list of string of hand's card

    Returns:
        (array): 3*4*15 numpy array
    '''
    # plane = np.zeros((3, 4, 15), dtype=int)
    plane = np.zeros((4, 10), dtype=int)
    for card in hand:
        card_info = card.split('-')
        color = COLOR_MAP[card_info[0]]
        trait = TRAIT_MAP[card_info[1]]
        plane[color][trait] = 0
    return plane

def encode_task(plane, task):
    ''' Encode target and represerve it into plane

    Args:
        plane (array): 1*4*15 numpy array
        target(str): string of target card

    Returns:
        (array): 1*4*15 numpy array
    '''
    for card in task:
        task_info = card.split('-')
        color = COLOR_MAP[task_info[0]]
        trait = TRAIT_MAP[task_info[1]]
        plane[color][trait] = 1
    return plane

def encode_target(plane, target):
    ''' Encode target and represerve it into plane
    Args:
        plane (array): 1*4*15 numpy array
        target(str): string of target card
    Returns:
        (array): 1*4*15 numpy array
    '''
    target_info = target.split('-')
    if target_info[0] == '10':
        return plane
    color = COLOR_MAP[target_info[0]]
    trait = TRAIT_MAP[target_info[1]]
    plane[color][trait] = 1
    return plane
