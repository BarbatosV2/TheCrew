# Game engine should run independently and wait for input from agent
# Should run with python engine.py Missions.csv
# Should be able to instantiate agents from a received message

import random
import os
import csv
import sys
import zmq
import json
import time

def suitAsText(suit):
    suitText = ''
    if suit == 0:
        suitText = 'Blue'
    elif suit == 1:
        suitText = 'Green'
    elif suit == 2:
        suitText = 'Pink'
    elif suit == 3:
        suitText = 'Yellow'
    elif suit == 4:
        suitText = 'Rocket'
    
    return suitText

def getUserInput():
    # Show user actions
    print("\n[1] See The Crew being played.")
    print("[q] Quit.")
    
    return input("What would you like to do? ")

# Import missions from a .csv file at path
def importMissions(path):
    with open(path, newline='') as csvfile:
        missionreader = csv.reader(csvfile, delimiter=',', quotechar= '|')
        missionRows = []
        for row in missionreader:
            stringRow = ', '.join(row)
            mixed = any(letter.islower() for letter in stringRow) \
                and any(letter.isupper() for letter in stringRow)
            if not mixed:
                missionRows.append(row)

        for row in missionRows:
            for index, cell in enumerate(row):
                if not cell:
                    row.pop(index)
        
        return missionRows

# Card can be numbered 1-9
# Have suit 0-4
# 0: Blue Circle
# 1: Green Triangle
# 2: Pink Square
# 3: Yellow X
# 4: Rocket(only numbered 1-4)
# Card can also be a task card

# Token can have value:
# 1-5, O (omega), > - >>>>
# Store value in string
# Empty string for no token
class Card:
    number = 0
    suit = 0
    isTask = False
    tokenValue = ''

    def __init__(self, number, suit, isTask):
        self.number = number
        self.suit = suit
        self.isTask = isTask

    # Function to set the task token on a task card
    def setToken(self, token):
        if ~self.isTask:
            print('Error: ' + str(self) + ' is not a task card')
            return
        self.tokenValue = token


class Mission:
    numTaskCards = 0
    taskCards = []
    taskTokens = []
    numAttempts = 0

    def __init__(self, numTaskCards, taskTokens):
        self.numAttempts = 0
        self.numTaskCards = numTaskCards
        self.taskTokens = taskTokens


class Game:
    agents = []
    missions = []
    taskCards = []
    playedCards = []
    agentLists = []
    commander = 0
    assignedTaskCards = [[],[],[],[]]
    completedTaskCards = []
    communicatedCards = []

    def __init__(self, missions, agents):
        self.missions = missions
        self.agents = agents

    # Utility function to show the cards of a agent
    def showCards(self, index):
        print('Agent ' + str(index) + ' cards:')
        for card in self.agents[index].cards:

            suitText = suitAsText(card.suit)
            
            print('Number: ' + str(card.number) +
                 ' Suit: ' + suitText)

    def sendEndMessage(self):
        for a_index, agent in enumerate(self.agents):
            # Connect to current agent
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect("tcp://localhost:" + str(5556 + a_index))
            data = {"complete": True}
            jsonData = json. dumps(data)
            socket.send_json(jsonData)
            socket.close()
            context.destroy()

    # Takes a task card and examines token
    # If token rule is valid returns True otherwise returns False
    def checkTaskToken(self, task, missionIndex):
        currentToken = task.tokenValue

        if len(self.completedTaskCards) == 0:
            if currentToken == '' or\
                currentToken == '1' or\
                currentToken == '<' or\
                currentToken == 'O' & self.missions[missionIndex].numTaskCards == 1:
                    return True
        else:
            prevToken = self.completedTaskCards[-1].tokenValue
            if currentToken == '':
                return True
            elif currentToken.isnumeric() &\
                prevToken.isnumeric():
                    if int(currentToken) - 1 == int(prevToken):
                        return True
                    else:
                        return False
            elif currentToken == 'O':
                size = 0
                for element in self.assignedTaskCards:
                    size += len(element)
                if size == 1:
                    return True
                else:
                    return False
            elif currentToken[0] == '>':
                flag = False
                for prevTask in self.completedTaskCards:
                    if prevTask.tokenValue[0] == '>' &\
                        len(currentToken) > len(prevTask.tokenValue):
                            flag = True
                return flag         

        # Tokens on played cards will only be either
        # Numeric and/or omega
        # OR Arrow
        # OR Omega

    # Generates the playing cards and distributes them to the agents
    def distributeCards(self):
        allCards = []
        for i in range(1, 10):
            for j in range(4):
                allCards.append(Card(i, j, False))

        for i in range(1, 5):
            allCards.append(Card(i, 4, False))

        random.shuffle(allCards)

        self.agentLists.clear()

        self.agentLists = [allCards[i * 10:(i + 1) * 10] 
            for i in range((len(allCards) + 9) // 10 )]

        for index, agent in enumerate(self.agents):
            # Send a message to the agent with a json array of the cards
            cardList = []
            for card in self.agentLists[index]:
                if card.number == 4 & card.suit == 4:
                    self.commander = index
                cardList.append(card.__dict__)
            
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect("tcp://localhost:" + str(5556 + index))
            socket.send_json(json.dumps(cardList))
            socket.close()
            context.destroy()

    # Generates the set of task cards and shuffles
    def generateTaskCards(self):
        self.taskCards.clear
        for i in range(1, 10):
            for j in range(4):
                self.taskCards.append(Card(i, j, True))
        
        random.shuffle(self.taskCards)
        print('Task cards generated...')

    # Assigns the task cards as layed out in the mission to the agents
    # Includes handing out tokens
    def assignTaskCards(self, missionIndex):
        for set in self.assignedTaskCards:
            set.clear()

        for i in range(self.missions[missionIndex].numTaskCards):
            card = self.taskCards.pop()
            if len(self.missions[missionIndex].taskTokens):
                card.setToken(self.missions[missionIndex].taskTokens.pop())
            self.missions[missionIndex].taskCards.append(card)

        i = self.getCommander()
        while len(self.missions[missionIndex].taskCards):
            if i < len(self.agents):
                self.assignedTaskCards[i] \
                    .append(self.missions[missionIndex].taskCards.pop())
                i = i + 1
                if i == len(self.agents):
                    i = 0
        
        print('Task cards assigned...')
            
    # Returns the index of the commander in the agents array
    def getCommander(self):
        return self.commander

    # Function to check if any cards of suit exist in hand
    def haveCardsOfSuit(self, suit, agent):
        for card in self.agentLists[agent]:
            if card.suit == suit:
                return True
        
        return False

    def removeCard(self, card, agent):
        for c, cardInHand in enumerate(self.agentLists[agent]):
            if card.suit == cardInHand.suit and card.number == cardInHand.number:
                self.agentLists[agent].pop(c)
                return

    def waitForComm(self):
        # Wait for agent communication in json form
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind("tcp://*:5555")
        comm = socket.recv_json()
        socket.close()
        context.destroy()
        pythonComm = json.loads(comm)

        print('Got comm')

        return pythonComm

    def checkCommunicatedCard(self, agent, card):
        allowedPosition = 0
        lowestNum = 10
        highestNum = 0
        suit = card["suit"]

        # Loop through cards and check if it is highest, lowest or only of suit
        for c in self.agentLists[agent]:
            if c.suit == suit:
                if c.number < lowestNum:
                    lowestNum = c.number
                elif c.number > highestNum:
                    highestNum = c.number

        if lowestNum == highestNum == card["number"]:
            allowedPosition = 1
        elif card["number"] == lowestNum:
            allowedPosition = 0
        elif card["number"] == highestNum:
            allowedPosition = 2
        else:
            allowedPosition = -1

        if allowedPosition != card["position"]:
            return False
        else:
            return True

    def readyForComm(self, firstAgent):
        currentAgent = firstAgent
        loopedOnce = False
        # Connect to agents and send ready message for comm
        while currentAgent < len(self.agents):
            if currentAgent == firstAgent:
                if loopedOnce:
                    break

            print('Ready for comm')
            print(currentAgent)
            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect("tcp://localhost:" + str(5556 + currentAgent))

            # Send ready state to agent
            socket.send_json({"ready": True})
            socket.close()
            context.destroy()
            print('Sent ready')

            communicatedCard = self.waitForComm()

            context = zmq.Context()
            socket = context.socket(zmq.REQ)
            socket.connect("tcp://localhost:" + str(5556 + currentAgent))

            while self.checkCommunicatedCard(currentAgent, communicatedCard) == False:
                # Ask for a new card to be communicated
                time.sleep(0.25)
                socket.send_json({"ready": False})
                communicatedCard = self.waitForComm()

            time.sleep(0.25)
            print("here")
            socket.send_json({"ready": True})

            socket.close()
            context.destroy()

            self.communicatedCards.append(communicatedCard)

            socket.close()
            context.destroy()
            currentAgent = currentAgent + 1
            if currentAgent == len(self.agents):
                currentAgent = 0
                loopedOnce = True
        
        return

    def playGame(self):
        # Loop through missions
        os.system('clear')
        for m_index, mission in enumerate(self.missions):
            print('New mission')
            firstCard = 0
            self.distributeCards()
            self.generateTaskCards()
            self.assignTaskCards(m_index)
            self.communicatedCards.clear()
            firstAgent = self.getCommander()

            # Starting with Commander
                # Each agent communicates?
                # Each agent plays card
                # Store each card in played cards
            currentAgent = firstAgent
            missionComplete = False

            time.sleep(0.25)
            self.readyForComm(firstAgent)
            
            currentAgent = firstAgent
            while True:
                if(missionComplete):
                    break
                print('New trick')
                print('------------------------------------------------------------')
                self.playedCards.clear()
                loopedOnce = False

                while currentAgent < len(self.agents):
                    if currentAgent == firstAgent:
                        if loopedOnce:
                            break
                    
                    # Connect to current agent
                    context = zmq.Context()
                    socket = context.socket(zmq.REQ)
                    socket.connect("tcp://localhost:" + str(5556 + currentAgent))

                    cards = [] # List of played cards this trick
                    taskCards = [[], [], [], []] # List of task cards for each player
                    communicatedCards = [] # List of communicated cards, one each player

                    #Build objects for current game state
                    for card in self.playedCards:
                        cards.append(card.__dict__)

                    for player in range(len(self.assignedTaskCards)):
                        for task in self.assignedTaskCards[player]:
                            taskCards.append(task.__dict__)

                    for comm in self.communicatedCards:
                        communicatedCards.append(comm)

                    state = [cards, taskCards, communicatedCards]

                    stateJson = json.dumps(state)

                    print('Curent played cards: ')
                    if len(cards):
                        for card in cards:
                            print(suitAsText(card["suit"]) + ' ' + str(card["number"]))

                    # Send game state to agent
                    time.sleep(0.05)
                    socket.send_json(stateJson)

                    # Wait for agent move in json form
                    socket = context.socket(zmq.REP)
                    socket.bind("tcp://*:5555")
                    move = socket.recv_json()
                    socket.close()
                    pythonMove = json.loads(move)
                    print('Agent ' + str(currentAgent) + ' played card: ' +\
                        suitAsText(pythonMove[0]['suit']) + ' ' + str(pythonMove[0]['number']))
                    if not isinstance(pythonMove, list):
                        print('Mission failed - out of cards')
                        return

                    pythonMove = pythonMove[0]
                    if len(self.playedCards):
                        idealSuit = self.playedCards[0].suit
                        if self.haveCardsOfSuit(idealSuit, currentAgent):
                            while pythonMove['suit'] != idealSuit:
                                print('Error card played does not follow rules of game...')
                                print('Getting new card from agent')

                                # Send agent message to resend card
                                socket = context.socket(zmq.REQ)
                                socket.connect("tcp://localhost:" + str(5556 + currentAgent))
                                socket.send_json({"newCard": True})
                                socket.close()

                                # Wait for agent move in json form
                                socket = context.socket(zmq.REP)
                                socket.bind("tcp://*:5555")
                                move = socket.recv_json()
                                socket.close()
                                pythonMove = json.loads(move)
                                pythonMove = pythonMove[0]

                    # Send agent message to not resend card
                    socket = context.socket(zmq.REQ)
                    socket.connect("tcp://localhost:" + str(5556 + currentAgent))
                    socket.send_json({"newCard": False})
                    socket.close()
                    context.destroy()
                    
                    playCard = Card(pythonMove["number"], pythonMove["suit"], \
                        pythonMove["isTask"])

                    self.playedCards.append(playCard)
                    self.removeCard(playCard, currentAgent)

                    if firstCard == 0:
                        firstCard = playCard
                    currentAgent = currentAgent + 1
                    if currentAgent == len(self.agents):
                        currentAgent = 0
                        loopedOnce = True
                    
                currentHighestCard = Card(0,0, False)
                currentWinningAgent = 0
                # Check the played cards
                for c_index, card in enumerate(self.playedCards):
                    if card.suit != firstCard.suit:
                        continue
                    if card.number > currentHighestCard.number:
                        currentHighestCard = card
                        # Current winning agent went (c_index)th
                        # So.... we need to check which agent went c_indexth
                        # To get correct agent
                        currentWinningAgent = firstAgent + c_index
                        if currentWinningAgent > len(self.agents):
                            currentWinningAgent = currentWinningAgent - len(self.agents)

                winningAgent = currentWinningAgent
                if winningAgent > len(self.agents) - 1:
                    winningAgent = winningAgent - len(self.agents)

                print('Winning agent is: ' + str(winningAgent))
                
                # Give the played cards to the agent who wins the trick
                # If wrong agent gets the card associated with a task, 
                # end game (lost)

                # Loop through task cards
                # If task card in played cards
                #   If task card in playedCards[winningAgent]
                #       Task complete
                #   Else
                #       Mission failed
                broken = False
                for t_index, agentTasks in enumerate(self.assignedTaskCards):
                    if broken:
                        break
                    for task in agentTasks:
                        if broken:
                            break
                        if not self.checkTaskToken(task, m_index):
                            self.sendEndMessage()
                            print('Task token rule broken - Mission failed')
                            return
                        for c_index, card in enumerate(self.playedCards):
                            if card.number == task.number and card.suit == task.suit:
                                print('Number: ' + str(task.number) + \
                                    ' suit: ' + suitAsText(task.suit))
                                # Task card in played cards
                                if t_index == winningAgent:
                                    self.completedTaskCards\
                                        .append(self.assignedTaskCards[winningAgent].pop())
                                    print('Task completed')
                                    currentAgent = winningAgent
                                    broken = True
                                    break
                                else:
                                    self.sendEndMessage()
                                    print('Task card in played cards')
                                    print('Mission failed')
                                    return
                
                # If all tasks complete, go to next mission (won)
                nextMission = True
                for a_index, agent in enumerate(self.agents):
                    if len(self.assignedTaskCards[a_index]):
                        nextMission = False

                if nextMission:
                    print('Mission complete')
                    missionComplete = True
                    self.sendEndMessage()
                    break
                    # Otherwise, keep playing, starting with agent who won next trick
        print('Game over you won')

numPlayers = 4
startMission = 0

def getUserInput():
    # Show current variables
    print('\nCurrent number of players: ' + str(numPlayers))
    print('Current starting mission: ' + str(startMission + 1))
    # Show user actions
    print("\n[1] See The Crew being played.")
    print("[2] Set the number of agents playing")
    print("[3] Select a mission to start")
    print("[4] Connect agents")
    print("[q] Quit.")
    
    return input("What would you like to do? ")

if __name__ == '__main__':
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")
    os.system('clear')

    print("\t**********************************************")
    print("\t******************* The Crew *****************")
    print("\t**********************************************")
    choice = ''
    playersIn = 0
    agents = {}
    while (choice != 'q'):
        choice = getUserInput()
        if choice == '2':
            numPlayers = int(input("How many players are playing? "))
            while numPlayers < 1 or numPlayers > 4:
                numPlayers = int(input("Please enter a number between 1 and 4... "))
        elif choice == '3':
            startMission = int(input("What mission would you like to start with? ")) - 1
            while startMission < 0:
                startMission = int(input("Please enter a number above 0... ")) - 1
        elif choice == '4':
            while playersIn < numPlayers:
                newAgent = socket.recv()
                agents[playersIn] = newAgent
                print('Agent connected: %s' % newAgent)
                socket.send(playersIn.to_bytes(1,sys.byteorder))
                playersIn += 1
            socket.close()
            context.destroy()
        elif choice == '1':
            os.system('clear')

            # Instantiate the mission
            mission = Mission(1, [])
            mission2 = Mission(2, [])
            missions = [mission, mission2]

            if(len(sys.argv) > 1):
                missionsList = importMissions(str(sys.argv[1]))
                csvMissions = []
                if missionsList:
                    for mission in missionsList:
                        for cell in mission:
                            if(not cell):
                                continue
                        tokens = []
                        if len(mission) > 1:
                            tokens.append(mission[1].join(',').join(mission[2:]))
                        newMission = Mission(int(mission[0]), tokens)
                        csvMissions.append(newMission)

            # Instantiate the game with the missions and agents
            game = Game(missions[startMission:], agents)
            game.playGame()
        elif choice == 'q':
            print('\nGoodbye')