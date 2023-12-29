class Card:
    number = 0
    suit = 0
    isTask = False
    tokenValue = ''

    info = {'color': [0, 1, 2, 3],
            'trait': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}

    def __init__(self, number, suit, isTask):
        self.number = number
        self.suit = suit
        self.isTask = isTask
        self.str = self.get_str()

    # Function to set the task token on a task card
    def setToken(self, token):
        if ~self.isTask:
            print('Error: ' + str(self) + ' is not a task card')
            return
        self.tokenValue = token

    def get_str(self):
        ''' Get the string representation of card
        Return:
            (str): The string of card's color and trait
        '''
        if self.suit == -1:
            return str(10) + '-' + str(10)
        return str(self.suit) + '-' + str(self.number)