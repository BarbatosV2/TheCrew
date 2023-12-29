
class Judger:

    @staticmethod
    def judge(players):
        ''' Judge the winner of the game

        Args:
            players (list): The list of players who play the game

        Returns:
            (list): The player id of the winner
        '''
        # self.np_random = np_random
        for player in players:
            if len(player.task) > 0:
                return -1
        return 1
