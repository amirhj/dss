# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.
import util
__author__ = "amir"
__date__ = "$Mar 10, 2015 6:32:49 PM$"

class QlearnerAgent:
	"""
	Abstract model for q-learner
	"""	
	def __init__(self):
		self.actions = []
		self.stateTemplate = {}
		self.qvalues = util.Counter()
		self.agents = []
		self.currentState = None
		self.terminated = False
		self.qstatesCounter = util.Counter()
		self.startState = None
		self.startHiddenState = None
		self.hiddenState = None		

	def getActions(self, state):
		return self.actions

	def getLegalActions(self, state):
		return self.actions

	def getStateTemplate(self):
		return self.stateTemplate

	def transitionReward(self, state, action):
		nextState = self.getTransition(state, action)
		return (nextState, self.getReward(state, action, nextState))

	def getTransition(self, state, action, test=True):
		return None
	
	def transit(self, state, action):
		nextState = self.getTransition(state, action, False)
		self.currentState = nextState
		self.qstatesCounter[(state, action)] += 1

	def getReward(self, state, action, nextState):
		return 0
	
	def setAgents(self, agents):
		self.agents = agents
		
	def changeState(self, state, value, index):
		newState = state[0:index]
		newState = newState + (value,)
		if index < len(state)-1:
			newState = newState + state[index+1:]
		return tuple(newState)
	
	def reciveMessage(self, key, value):
		pass
	
	def sendMessage(self, key, value):
		for agent in self.agents:
			if agent.id != self.id:
				agent.reciveMessage(key, value)
	
	def reset(self):
		self.currentState = self.startState
		if self.startHiddenState != None:
			self.hiddenState = self.startHiddenState.copy()
		self.terminated = False
		