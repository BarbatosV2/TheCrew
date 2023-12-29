from copy import deepcopy
from rlcard.games.the_crew.utils import init_deck, init_task


class Dealer:
    ''' Initialize a uno dealer class
    '''
    def __init__(self, np_random):
        self.np_random = np_random
        self.deck = init_deck()
        self.task = init_task()
        self.shuffle()

    def shuffle(self):
        ''' Shuffle the deck
        '''
        self.np_random.shuffle(self.deck)

    def deal_cards(self, player, num):
        for _ in range(num):
            player.hand.append(self.deck.pop())

    def deal_tasks(self, player, num):
        for _ in range(num):
            player.task.append(self.task.pop())

    def alltasks(self, players, task):
        a = task[(len(task)-4):]
        for player in players:
            for _ in range(len(a)):
                player.atask.append(a[_])

