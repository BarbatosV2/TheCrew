from rlcard.games.the_crew.card import Card
from rlcard.games.the_crew.utils import cards2list
from rlcard.games.the_crew.judger import Judger

class Round:

    def __init__(self, dealer, num_players, np_random):
        ''' Initialize the round class

        Args:
            dealer (object): the object of UnoDealer
            num_players (int): the number of players in game
        '''
        self.np_random = np_random
        self.dealer = dealer
        self.target = Card(-1, -1, False)
        self.current_player = 0
        self.num_players = num_players
        self.direction = 1
        self.trick_cards = []
        self.played_cards = []
        self.is_over = False
        self.payoffs = [0 for _ in range(self.num_players)]

    def maxIndex(self, cards):
        suit = cards[0].suit
        value = []
        for card in cards:
            if card.suit == suit:
                value.append(card.number)
            if card.suit != suit and card.number != 9:
                value.append(-1)
            if card.suit != suit and card.number == 9:
                value.append(card.suit + 10)
        return value.index(max(value))

    def win_trick(self, tricks, tasks, atask):
        a = -1
        b = -1
        for task in tasks:
            for cardomh in tricks:
                if task.suit == cardomh.suit and task.number == cardomh.number:
                    a = tasks.index(task)
                    i = 0
                    for hey in atask:
                        if task.str == hey.str:
                            break
                        i += 1
                    tasks.pop(a)
                    atask.pop(i)
                    return tasks, atask, 2
        for task in atask:
            for card in tricks:
                passing = False
                if task.suit == card.suit and task.number == card.number:
                    for mtask in tasks:
                        if mtask == task:
                            passing = True
                        break
                    if passing:
                        break
                    return tasks, atask, -2

        return tasks, atask, 1

    def proceed_round(self, players, action):
        ''' Call other Classes's functions to keep one round running

        Args:
            player (object): object of UnoPlayer
            action (str): string of legal action
        '''
        player = players[self.current_player]
        card_info = action.split('-')
        color = card_info[0]
        trait = card_info[1]
        # remove correspongding card
        remove_index = None

        for index, card in enumerate(player.hand):
            if color == str(card.suit) and trait == str(card.number):
                remove_index = index

        card = player.hand.pop(remove_index)

        if not player.hand:
            self.is_over = True
            self.loser = [self.current_player]

        self.trick_cards.append(card)
        self.played_cards.append(card)

        if len(self.trick_cards) == 1:
            self.target = card

        if len(self.trick_cards) == self.num_players:
            max_index = self.maxIndex(self.trick_cards)
            dis = self.num_players - 1 - max_index
            for i in range(dis):
                self.current_player = (self.current_player - 1) % self.num_players
            a, b, c = self.win_trick(self.trick_cards, players[self.current_player].task,
                                     players[self.current_player].atask)
            if c == 1:
                self.payoffs[self.current_player] += 1
            elif c == 2:
                self.payoffs[self.current_player] += 2
                players[self.current_player].task = a
                players[self.current_player].atask = b
            elif c == -2:
                self.payoffs[self.current_player] += -2
                self.is_over = True
            self.trick_cards = []
        else:
            self.current_player = (self.current_player + self.direction) % self.num_players
            self.target = card

    def get_legal_actions(self, players, player_id):
        legal_actions = []
        hand = players[player_id].hand
        same = True
        target = self.target

        for card in hand:
            if card.suit == target.suit:
                same = False
                legal_actions.append(card.str)

        if same is False:
            for card in hand:
                if card.number == 9:
                    legal_actions.append(card.str)

        if same is True:
            for card in hand:
                legal_actions.append(card.str)

        return legal_actions

    def get_state(self, players, player_id):
        ''' Get player's state

        Args:
            players (list): The list of UnoPlayer
            player_id (int): The id of the player
        '''
        state = {}
        player = players[player_id]
        state['hand'] = cards2list(player.hand)
        state['target'] = self.target.str
        state['trick_cards'] = cards2list(self.trick_cards)
        state['played_cards'] = cards2list(self.played_cards)
        state['legal_actions'] = self.get_legal_actions(players, player_id)
        state['task'] = cards2list(player.task)
        state['atask'] = cards2list(player.atask)
        return state
