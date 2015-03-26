import QLearnerModel
from random import choice

class DistributedRGCAgent(QLearnerModel.QlearnerAgent):
	colors = ['C1','C2','C3']
	
	def __init__(self, rightN, leftN):
		QLearnerModel.QlearnerAgent.__init__(self)
		
		self.actions = ['read-rn', 'read-ln', 'changeColor', 'no-action']
		
		self.stateTemplate = {'color':DistributedRGCAgent.colors,\
							'rn-color':DistributedRGCAgent.colors,\
							'ln-color':DistributedRGCAgent.colors}
							#'rn-color-diff': [True,False],\
							#'ln-color-diff': [True,False],\}
		
		self.rightN = rightN
		self.leftN = leftN
		
		self.pallet = set()
		self.index = None
		
	def getTransition(self, state, action, test=True):
		newState = state
		
		if action == 'changeColor':
			newState = self.changeState(state, self.changeColor(state), 0)
		elif action == 'read-rn':
			newState = self.changeState(newState, self.readNeighborColor('right'),1)
		elif action == 'read-ln':
			newState = self.changeState(newState, self.readNeighborColor('left'),2)
		
		return newState
	
	def changeColor(self, state):
		if state[0] in self.pallet:
			self.pallet.remove(state[0])	
		if len(self.pallet) == 0:
			self.pallet = set(DistributedRGCAgent.colors)
		if state[0] in self.pallet:
			self.pallet.remove(state[0])
		return choice(list(self.pallet))
	
	def readNeighborColor(self,n):
		if n == 'right':
			return self.rightN.currentState[0]
		elif n == 'left':
			return self.leftN.currentState[0]
		
	def getReward(self, state, action, nextState):
		reward = 0
		
		if state[1] != self.readNeighborColor('right') or state[2] != self.readNeighborColor('left'):
			if state[1] != self.readNeighborColor('right') and action != 'read-rn':
				reward += -15
				
			if state[2] != self.readNeighborColor('left') and action != 'read-ln':
				reward += -15
		else:
			if nextState[0] == nextState[1]:
				reward += -10
			
			if nextState[0] == nextState[2]:
				reward += -10
			
			if nextState[0] != nextState[1] and nextState[0] != nextState[2]:
				reward += 20		
		
		return reward
	
	def reset(self):
		QLearnerModel.QlearnerAgent.reset(self)
		self.pallet = set(DistributedRGCAgent.colors)
			