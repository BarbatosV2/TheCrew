import json
import os
from random import randint
import zmq
import multiprocessing as mp
import sys
import rlcard

class Agent:
    isCommander = False
    tasks = []
    cards = []
    commUsed = False
    position = 0
    gameState = []

    rlCardAgent = None

    def __init__(self, position, agent):
        self.commUsed = False
        self.tasks = []
        self.position = position
        self.rlCardAgent = agent
        self.waitForCards()

    # Position can be 0 for lowest, 1 for only card, 2 for highest
    # Function to use the agent's comm token on a card
    def useCommToken(self, card):
        position = 0
        lowestNum = 10
        highestNum = 0
        suit = card["suit"]

        # Loop through cards and check if it is highest, lowest or only of suit
        for c in self.cards:
            if c["suit"] == suit:
                if c["number"] < lowestNum:
                    lowestNum = c["number"]
                elif c["number"] > highestNum:
                    highestNum = c["number"]

        if lowestNum == highestNum == card["number"]:
            position = 1
        elif card["number"] == lowestNum:
            position = 0
        elif card["number"] == highestNum:
            position = 2
        else:
            position = -1

        comm = {"number": card["number"], "suit": card["suit"], "position": position}
        self.commUsed = True

        return comm

    def waitForComm(self):
        print('Waiting for comm ready')
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind("tcp://*:" + str(5556 + self.position))

        message = socket.recv_json()
        socket.close()
        context.destroy()

        print(message)
        if message["ready"] == True:
            print('Comm ready')
            return

    def sendComm(self):
        randomCard = self.cards[randint(0, len(self.cards) - 1)]
        if not self.commUsed:
            print('Use comm')
            comm = self.useCommToken(randomCard)

            while (comm["position"] == -1):
                randomCard = self.cards[randint(0, len(self.cards) - 1)]
                comm = self.useCommToken(randomCard)

            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect("tcp://localhost:5555")
            socket.send_json(json.dumps(comm))
            socket.close()
            context.destroy()

            print("Waiting for done ready")

            context = zmq.Context()
            socket = context.socket(zmq.REP)
            socket.bind("tcp://*:" + str(5556 + self.position))

            done = socket.recv_json()

            socket.close()
            context.destroy()

            if done["ready"] == False:
                self.commUsed = False
                self.sendComm()
            else:
                return

    def waitForCards(self):
        print('Waiting for cards...')
        self.cards.clear()
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind("tcp://*:" + str(5556 + self.position))

        cards = socket.recv_json()
        socket.close()
        context.destroy()

        self.cards = json.loads(cards)

        print('Got cards...')

        self.waitForComm()

        self.sendComm()

        self.waitForMessage()

    def waitForMessage(self):
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind("tcp://*:" + str(5556 + self.position))
        print(str(self.position) + ' Waiting for message...')
        
        gameState = socket.recv_json()

        print('Got message...')
        print('------------------------------------------------------------')

        state = json.loads(gameState)
        self.gameState = state

        print('Current game state:')
        print(state)
        
        if not isinstance(state, list):
            if state['complete']:
                socket.close()
                context.destroy()
                print('Got complete messa;ge...')
                self.commUsed = False
                self.waitForCards()
                return

        socket.close()

        socket = context.socket(zmq.REQ)
        socket.connect("tcp://localhost:5555")
        card = self.chooseCard()
        # Send the chosen card to the engine
        socket.send_json(json.dumps(card))
        socket.close()

        # Wait to see if we need to play a different card
        socket = context.socket(zmq.REP)
        socket.bind("tcp://*:" + str(5556 + self.position))
        message = socket.recv_json()
        socket.close()
        needToPlayDifferentCard = message["newCard"]

        while needToPlayDifferentCard:
            # Put card back and play a different card
            self.cards.append(card[0])
            socket = context.socket(zmq.REQ)
            socket.connect("tcp://localhost:5555")
            card = self.chooseCard()
            # Send the chosen card to the engine
            socket.send_json(json.dumps(card))
            socket.close()

            # Wait to see if we need to play a different card
            socket = context.socket(zmq.REP)
            socket.bind("tcp://*:" + str(5556 + self.position))
            message = socket.recv_json()
            socket.close()
            needToPlayDifferentCard = message["newCard"]

        context.destroy()

        print('Sent response...')
        self.waitForMessage()

    def chooseCard(self):
        if self.rlCardAgent:
            # Run the eval step for the state to get the agent's move
            move = self.rlCardAgent.eval_step(self.gameState)
        else:
            chosenCard = ''
            if len(self.cards):
                num = randint(0, len(self.cards) - 1)
                chosenCard = [self.cards.pop(num)]

            if len(self.gameState[0]):
                idealSuit = self.gameState[0][0]
                idealSuit = int(idealSuit['suit'])
                if self.haveCardsOfSuit(idealSuit):
                    if chosenCard[0]['suit'] != idealSuit:
                        self.cards.append(chosenCard[0])
                        chosenCard = self.chooseCard()

            return chosenCard

    # Function to check if any cards of suit exist in hand
    def haveCardsOfSuit(self, suit):
        for card in self.cards:
            if card["suit"] == suit:
                return True
        
        return False

if __name__ == "__main__":
    context = zmq.Context()

    agents = {}

    if(len(sys.argv) > 1):
        for i in range(int(sys.argv[1])):
            print("Connecting to game engine")
            socket = context.socket(zmq.REQ)
            socket.connect("tcp://localhost:5555")

            socket.send_string('Hello ' + str(i))

            message = socket.recv()

            position = int.from_bytes(message, "big")

            # Run this function once per agent with the model path for each agent
            def load_model(model_path, device=None):
                agent = None
                if os.path.isfile(model_path):  # Torch model
                    import torch
                    agent = torch.load(model_path, map_location=device)
                    agent.set_device(device)
                
                return agent

            # testAgent = load_model('agents/agents.file.here')

            agents[i] = mp.Process(target=Agent, name='Agent' + str(i), args=(position, load_model('None')))
            print(agents[i])
            
            agents[i].start()
