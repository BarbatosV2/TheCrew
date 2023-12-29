# Constrained Co-operative Agents
## The Crew - Group 4

A python application to run the Crew game

### Running the application

The dependencies for RLCard and the Agents4 repositories first need to be installed.

Run `pip3 install -r requirements.txt` from this directory to install the requirements for the Agents4 repository.

Run `python3 engine.py` from this directory to run the engine with 2 sample missions. These missions have 1 and 2 tasks respectively and no task tokens. From the engine interface, you can then choose to change the number of agents playing, change the starting mission and wait for the agents to connect. Once the agents are connected, you can then see them play the game.

Run `python3 engine.py Missions.csv` to run the application with the missions as set out in the `Missions.csv` file. Currently, only the missions with a number of task cards and task tokens are able to be imported. Any missions with more complicated rules are ignored at this stage.

Using a second terminal, run `python3 agents.py 4` from this directory to run the application with 4 agents. The agents will then connect to the engine, as long as the engine is waiting. And then the engine will go back to the menu to wait for the game to play.

### Engine
The engine process contains the logic for playing the game and sending information to the agents. It contains the missions that can also be loaded from a CSV file as well as the task cards for that mission. The engine also controls any logic around distributing cards and handling the communication between agents, as this is not directly allowed. It can be interfaced with through the command line.

### Agent
Each agent process contains the logic for deciding a move to make. It receives messages from the engine process, which give it messages about the cards that have been played before and the rest of the game state. It alone does not include its task cards. It sends a move to the engine when it is its turn. Each agent runs in its own process.

### Agent - Engine communication

The agents and the game engine communicate via Transmission Control Protocol (TCP) using the [ZeroMQ library](zeromq.org)[[1]](#1).
The game engine runs on port 5555 and each agent runs on port 5556 to 5559.
JavaScript Object Notation (JSON) objects are used to communicate the game state and card played by the agent, for example, when communicating the players cards, a JSON array will be specified with each card as:
`{"number": 1, "suit": 2, "isTask": False}`
The agents are then able to receive this object and build a dictionary of cards that they can then use to make decisions.

## Training Agents with RLCard
The [RLCard](https://github.com/datamllab/rlcard)[[2]](#2) framework is used in this repository for training agents to play The Crew.

If you would like to train your own agents, run `pip3 install -e .` and then `pip3 install -e .[torch]` from this directory to install the requirements for the RLCard repository.

In order to run the training, use `python3 startTraining.py`. This will create a trained model in the `experiments` folder under `model.pth`. This will then be used in the running agents file for the agents to play the Crew autonomously.

## References

<a id="1">[1]</a> 
The ZeroMQ Authors (2021). 
ZeroMQ,
2021

<a id="2">[2]</a> 
Zha, Daochen and Lai, Kwei-Herng and Huang, Songyi and Cao, Yuanpu and Reddy, Keerthana and Vargas, Juan and Nguyen, Alex and Wei, Ruzhe and Guo, Junyu and Hu, Xia (2020). 
RLCard: A Platform for Reinforcement Learning in Card Games,
IJCAI,
2020

