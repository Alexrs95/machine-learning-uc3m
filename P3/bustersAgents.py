# bustersAgents.py
# ----------------

import util
from game import Agent
from game import Directions
from keyboardAgents import KeyboardAgent
import inference
import busters
import sys

class NullGraphics:
    "Placeholder for graphics"
    def initialize(self, state, isBlue = False):
        pass
    def update(self, state):
        pass
    def pause(self):
        pass
    def draw(self, state):
        pass
    def updateDistributions(self, dist):
        pass
    def finish(self):
        pass

class KeyboardInference(inference.InferenceModule):
    """
    Basic inference module for use with the keyboard.
    """
    def initializeUniformly(self, gameState):
        "Begin with a uniform distribution over ghost positions."
        self.beliefs = util.Counter()
        for p in self.legalPositions: self.beliefs[p] = 1.0
        self.beliefs.normalize()

    def observe(self, observation, gameState):
        noisyDistance = observation
        emissionModel = busters.getObservationDistribution(noisyDistance)
        pacmanPosition = gameState.getPacmanPosition()
        allPossible = util.Counter()
        for p in self.legalPositions:
            trueDistance = util.manhattanDistance(p, pacmanPosition)
            if emissionModel[trueDistance] > 0:
                allPossible[p] = 1.0
        allPossible.normalize()
        self.beliefs = allPossible

    def elapseTime(self, gameState):
        pass

    def getBeliefDistribution(self):
        return self.beliefs


class BustersAgent:
    "An agent that tracks and displays its beliefs about ghost positions."

    def __init__( self, index = 0, inference = "ExactInference", ghostAgents = None, observeEnable = True, elapseTimeEnable = True):
        inferenceType = util.lookup(inference, globals())
        self.inferenceModules = [inferenceType(a) for a in ghostAgents]
        self.observeEnable = observeEnable
        self.elapseTimeEnable = elapseTimeEnable

    def registerInitialState(self, gameState):
        "Initializes beliefs and inference modules"
        import __main__
        self.display = __main__._display
        for inference in self.inferenceModules:
            inference.initialize(gameState)
        self.ghostBeliefs = [inf.getBeliefDistribution() for inf in self.inferenceModules]
        self.firstMove = True

    def observationFunction(self, gameState):
        "Removes the ghost states from the gameState"
        agents = gameState.data.agentStates
        #gameState.data.agentStates = [agents[0]] + [None for i in range(1, len(agents))]
        return gameState

    def getAction(self, gameState):
        "Updates beliefs, then chooses an action based on updated beliefs."
        for index, inf in enumerate(self.inferenceModules):
            if not self.firstMove and self.elapseTimeEnable:
                inf.elapseTime(gameState)
            self.firstMove = False
            if self.observeEnable:
                inf.observeState(gameState)
            self.ghostBeliefs[index] = inf.getBeliefDistribution()
        self.display.updateDistributions(self.ghostBeliefs)
        return self.chooseAction(gameState)

    def chooseAction(self, gameState):
        "By default, a BustersAgent just stops.  This should be overridden."
        return Directions.STOP

class BustersKeyboardAgent(BustersAgent, KeyboardAgent):
    "An agent controlled by the keyboard that displays beliefs about ghost positions."

    def __init__(self, index = 0, inference = "KeyboardInference", ghostAgents = None):
        KeyboardAgent.__init__(self, index)
        BustersAgent.__init__(self, index, inference, ghostAgents)

    def getAction(self, gameState):
        return BustersAgent.getAction(self, gameState)

    def chooseAction(self, gameState):
        return KeyboardAgent.getAction(self, gameState)

from distanceCalculator import Distancer
from game import Actions
from game import Directions
import random, sys
     
class P3QLearning(BustersAgent):
    "An agent that charges the closest ghost."

    def __init__(self, index = 0, inference = "ExactInference", ghostAgents = None):
        BustersAgent.__init__(self, index, inference, ghostAgents)
        self.q_table = self.initQTable()
        self.epsilon = 0.3
        self.alpha = 0.8
        self.discount = 0.8
        self.actions = [Directions.NORTH, Directions.WEST, Directions.SOUTH, Directions.EAST]
        self.lastState = None
        self.lastAction = None
        self.numGhosts = 4
        self.lastDistance = 100
        self.turns = 0
        self.reward = 0

        #para cada par q_table[(state, action)] habra un valor. 

    def registerInitialState(self, gameState):
        BustersAgent.registerInitialState(self, gameState)
        self.distancer = Distancer(gameState.data.layout, False)

    def getAction(self, gameState):
        return self.chooseAction(gameState)

    def getState(self, gameState):
        self.reward = 0
        state = ""
        ghostDist = []
        for i in range(len(gameState.livingGhosts)):
            if gameState.livingGhosts[i] is True:
                ghostDist.append(gameState.getGhostPosition(i))

        pacmanPosition = gameState.getPacmanPosition()
        dists = []
        for i in ghostDist:
            dists.append(self.distancer.getDistance(pacmanPosition, i))

        #get the index of the nearest ghost
        index = dists.index(min(dists))

        if min(dists) < self.lastDistance:
		self.reward = 5

        #get the vector between pacman and the nearest ghost        
        vec = (pacmanPosition[0] - ghostDist[index][0], pacmanPosition[1] - ghostDist[index][1])
        if vec[0] > 0:
            if vec[1] > 0:
                #print "down left",
                if abs(vec[0]) > abs(vec[1]):
                    state += Directions.WEST
                else:
                    state += Directions.SOUTH
            else:
                #print "up left",
                if abs(vec[0]) > abs(vec[1]):
                    state += Directions.WEST
                else:
                    state += Directions.NORTH
        else:
            if vec[1] > 0:
                #print "down right", 
                if abs(vec[0]) > abs(vec[1]):
                    state += Directions.EAST
                else:
                    state += Directions.SOUTH
            else:
                #print "up right",
                if abs(vec[0]) > abs(vec[1]):
                    state += Directions.EAST
                else:
                    state += Directions.NORTH

        state += ","

        state +=\
        str(gameState.hasWall(gameState.getPacmanPosition()[0], gameState.getPacmanPosition()[1] + 1)) + "," +\
        str(gameState.hasWall(gameState.getPacmanPosition()[0] - 1, gameState.getPacmanPosition()[1])) + "," +\
        str(gameState.hasWall(gameState.getPacmanPosition()[0], gameState.getPacmanPosition()[1] - 1)) + "," +\
        str(gameState.hasWall(gameState.getPacmanPosition()[0] + 1, gameState.getPacmanPosition()[1])) 

        return state

    def shouldExit(self):
        return self.turns >= 800

    def chooseAction(self, gameState):
        #if the number of turns is bigger than a constant
        #if self.shouldExit():
        #    sys.exit(0)

        #get the current state
        state = self.getState(gameState)
        
        #get the action
        legalActions = self.getLegalActions(state)
        action = None
        if util.flipCoin(self.epsilon):
            action = self.getPolicy(state)
        else:
            action = random.choice(legalActions)

        #update the table
        if self.lastState != None and self.lastAction != None:
            #if a ghost has been eaten
            if sum(gameState.livingGhosts) < self.numGhosts:
                numGhosts = sum(gameState.livingGhosts)
                self.reward = 100
            self.update(self.lastState, self.lastAction, state, self.reward)

        #update values
        self.lastState = state
        self.lastAction = action
        self.turns += 1
        return action

    def getPolicy(self, state):
        return self.computeActionFromQValues(state)

    def getLegalActions(self, state):
        legalActions = []
        state = state.split(",")[1:]
        for i,s in enumerate(state):
            if s == "False":
                legalActions.append(self.actions[i])
        return legalActions


    def getValue(self, state):
        return self.computeValueFromQValues(state)

    def computeValueFromQValues(self, state):
        """
          Returns max_action Q(state,action)
          where the max is over legal actions.  Note that if
          there are no legal actions, which is the case at the
          terminal state, you should return a value of 0.0.
        """
        legalActions = self.getLegalActions(state)
        if len(legalActions) == 0:
          return 0.0
        tmp = []
        for action in legalActions:
          tmp.append(self.computeQValueFromValues(state, action))
        return max(tmp)


    def computeActionFromQValues(self, state):
        """
          Compute the best action to take in a state.  Note that if there
          are no legal actions, which is the case at the terminal state,
          you should return None.
        """
        legalActions = self.getLegalActions(state)
        if len(legalActions)==0:
          return None
        tmp = util.Counter()
        for action in legalActions:
          tmp[action] = self.computeQValueFromValues(state, action)
        return tmp.argMax()

    def computeQValueFromValues(self, state, action):
        """
          Returns Q(state,action)
          Should return 0.0 if we have never seen a state
          or the Q node value otherwise
        """
        "*** YOUR CODE HERE ***"
        return self.q_table[(state, action)]


    def initQTable(self):
        table_file = open("qtable.txt", "r")
        table_file.seek(0)
        table = table_file.readlines()
        qvalues = []
        for i, line in enumerate(table):
            qvalues.append(line)
        table_file.close()

        q_table = util.Counter()
        dirs = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]
        walls = ["True", "False"]
        actions = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]
        i = 0
        for direction in dirs:
            for wall1 in walls:
                for wall2 in walls:
                    for wall3 in walls:
                        for wall4 in walls:
                            for action in actions:
                                state = direction + "," + wall1 + "," + wall2 + ","+ wall3 + ","+ wall4
                                q_table[(state, action)] = float(qvalues[i])
                                i += 1
        return q_table

    def update(self, state, action, nextState, reward):
        self.q_table[(state,action)] = (1 - self.alpha) * self.q_table[(state, action)] +\
            self.alpha * (reward + self.discount*self.getValue(nextState))

    def writeQtable(self):
        table_file = open("qtable.txt", "w+")
        for key in self.q_table:
            table_file.write(str(self.q_table[key])+"\n")
        table_file.close()

    def __del__(self):
        self.writeQtable()  

from learningAgents import ReinforcementAgent

"""
      Q-Learning Agent

      Instance variables you have access to
        - self.epsilon (exploration prob)
        - self.alpha (learning rate)
        - self.discount (discount rate)

      Functions you should use
        - self.getLegalActions(state)
          which returns legal actions for a state
"""
        
class QLearningAgent(ReinforcementAgent, BustersAgent):
    "An agent that charges the closest ghost."
    """
        These default parameters can be changed from the pacman.py command line.
        For example, to change the exploration rate, try:
           
        QTable   - QTable
        alpha    - learning rate
        epsilon  - exploration rate
        gamma    - discount factor
        numTraining - number of training episodes, i.e. no learning after these many episodes
        """
        
    def __init__( self, index = 0, inference = "ExactInference", ghostAgents = None, observeEnable = True, elapseTimeEnable = True):
        ReinforcementAgent.__init__(self)
        inferenceType = util.lookup(inference, globals())
        self.inferenceModules = [inferenceType(a) for a in ghostAgents]
        self.observeEnable = observeEnable
        self.elapseTimeEnable = elapseTimeEnable

        
    def registerInitialState(self, gameState):
        "Pre-computes the distance between every two points."
        BustersAgent.registerInitialState(self, gameState)
        self.distancer = Distancer(gameState.data.layout, False)

    def getValue(self, state):
        """
          Return the value of the state (computed in __init__).
        """
        return self.values[state]


    def computeQValueFromValues(self, state, action):
        """
          Compute the Q-value of action in state from the
          value function stored in self.values.
        """
        "*** YOUR CODE HERE ***"
        util.raiseNotDefined()
    
    def chooseAction(self, gameState):
        """
          Compute the best action to take in a state.  Note that if there
          are no legal actions, which is the case at the terminal state,
          you should return None.
        """
        util.raiseNotDefined()
        
    def update(self, state, action, nextState, reward):
        """
          The parent class calls this to observe a
          state = action => nextState and reward transition.
          You should do your Q-Value update here

          NOTE: You should never call this function,
          it will be called on your behalf
        """
        "*** YOUR CODE HERE ***"
        util.raiseNotDefined()
        
    def getPolicy(self, state):
        return self.chooseAction(state)

    def getAction(self, state):
        "Returns the policy at the state (no exploration)."
        return self.chooseAction(state)

    def getQValue(self, state, action):
        return self.computeQValueFromValues(state, action)


class PacmanQAgent(QLearningAgent):
    "Exactly the same as QLearningAgent, but with different default parameters"

    def __init__(self, **args):
        self.index = 0  # This is always Pacman
        QLearningAgent.__init__(self, **args)
        self.q_table = self.initQTable()
        self.lastState = None
        self.episodeRewards = 0
        self.alpha = 0.3
        self.discount = 0.8
        self.epsilon = 0.8
        self.turns = 0

    def shouldExit(self):
        return self.turns >= 2000

    def getAction(self, state):
        """
        Simply calls the getAction method of QLearningAgent and then
        informs parent of action for Pacman.  Do not change or remove this
        method.
        """
        self.turns += 1
        #if self.shouldExit():
        #    sys.exit(0)

        legalActions = state.getLegalActions(0)
        legalActions.remove(Directions.STOP)

        action = None
        if util.flipCoin(self.epsilon):
	       action = self.getPolicy(state)
        else:
            action = random.choice(legalActions)
        self.doAction(state,action)
        return action

    def getPolicy(self, state):
        return self.chooseAction(state)

    def chooseAction(self, gameState):
        legalActions = gameState.getLegalActions(0)
        legalActions.remove(Directions.STOP)

        tmp = util.Counter()
        for action in legalActions:
          tmp[action] = self.getQValue(gameState, action)
        return tmp.argMax()

    def getQValue(self, state, action):
        return self.computeQValueFromValues(self.getState(state), action)

    def computeQValueFromValues(self, state, action):
        return self.q_table[(state, action)]

    def getNearestGhostDist(self, gameState):
        ghostDist = []
        for i in range(len(gameState.livingGhosts)):
            if gameState.livingGhosts[i] is True:
                ghostDist.append(gameState.getGhostPosition(i))

        pacmanPosition = gameState.getPacmanPosition()
        dists = []
        for i in ghostDist:
            dists.append(self.distancer.getDistance(pacmanPosition, i))

        #get the index of the nearest ghost
        return min(dists)


    def update(self, state, action, nextState, reward):
        """
          The parent class calls this to observe a
          state = action => nextState and reward transition.
          You should do your Q-Value update here

          NOTE: You should never call this function,
          it will be called on your behalf
        """
        "*** YOUR CODE HERE ***"
        if reward < 0:
            if self.getNearestGhostDist(nextState) < self.getNearestGhostDist(state):
                reward = 10
        #print "reward", reward, "Action:", action, "State:", self.getState(state)
        self.q_table[(self.getState(state), action)] = (1 - self.alpha) * self.q_table[(self.getState(state),action)] +\
            self.alpha * (reward + self.discount * self.getValue(nextState))


    def getValue(self, state):
        """
          Return the value of the state (computed in __init__).
        """
        legalActions = state.getLegalActions(0)
        if Directions.STOP in legalActions:
            legalActions.remove(Directions.STOP)

        tmp = []
        for action in legalActions:
          tmp.append(self.computeQValueFromValues(self.getState(state), action))
        if len(tmp) == 0:
            return 0
        return max(tmp)

    def getState(self, gameState):
        state = ""
        ghostDist = []
        for i in range(len(gameState.livingGhosts)):
            if gameState.livingGhosts[i] is True:
                ghostDist.append(gameState.getGhostPosition(i))

        pacmanPosition = gameState.getPacmanPosition()
        dists = []
        for i in ghostDist:
            dists.append(self.distancer.getDistance(pacmanPosition, i))

        #get the index of the nearest ghost
        index = dists.index(min(dists))

        #get the vector between pacman and the nearest ghost        
        vec = (pacmanPosition[0] - ghostDist[index][0], pacmanPosition[1] - ghostDist[index][1])
        if vec[0] > 0:
            if vec[1] > 0:
                #print "down left",
                state += Directions.WEST + "," + Directions.SOUTH + ","
            else:
                #print "up left",
                state += Directions.WEST + "," + Directions.NORTH + ","
        else:
            if vec[1] > 0:
                #print "down right", 
                state += Directions.EAST + "," + Directions.SOUTH + ","
            else:
                #print "up right",
                state += Directions.EAST + "," + Directions.NORTH + ","
                
        state += gameState.data.agentStates[0].getDirection()

        return state

    def initQTable(self):
        table_file = open("qtable.txt", "r")
        table_file.seek(0)
        table = table_file.readlines()
        qvalues = []
        for i, line in enumerate(table):
            qvalues.append(line)
        table_file.close()

        q_table = util.Counter()
        dirs = [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]
        i = 0
        for direction in dirs:
            for direction2 in dirs:
                for direction3 in dirs:
                    for action in dirs:
                        state = direction + "," + direction2 + "," + direction3
                        q_table[(state, action)] = float(qvalues[i])
                        i += 1
        return q_table

    def writeQtable(self):
        table_file = open("qtable.txt", "w+")
        for key in self.q_table:
            table_file.write(str(self.q_table[key])+"\n")
        table_file.close()

    def __del__(self):
        self.writeQtable()  



