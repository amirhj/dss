import random
from DistributedMutexAgent import DistributedMutexAgent
import util

class DistributedQLearner:
	def __init__(self, numberOfAgents, sharedModel=False, gamma=0.8, alpha=0.95, epsilon=0.1, iteration=500):
		self.gamma = gamma
		self.alpha = alpha
		self.epsilon = epsilon
		self.iteration = iteration
		self.agents = []
		self.numberOfAgents = numberOfAgents
		self.sharedModel = sharedModel
	
	def createAgents(self, qlearner):
		qlearner = globals()[str(qlearner)]
		for i in range(self.numberOfAgents):
			agent = qlearner()
			agent.id = 'Agent'+str(i)
			self.agents.append(agent)
			
		if self.sharedModel:
			stateSpace = self.agents[0].qstates
			for i in range(1, self.numberOfAgents):
				self.agents[i].qstates = stateSpace
				
	def run(self):
		log = Logger(fileOutput=True)
		for i in range(self.iteration):
			activeAgents = self.numberOfAgents
			log.log("iteration %d ***************************************" % (i+1,),2)
			while activeAgents > 0:
				ai = -1
				for a in self.agents:
					ai += 1
					if not a.terminated:
						actions = set(a.getLegalActions(a.currentState))
						qvalues = {}
						maxq = None
						maxActions = []
						
						log.log(str(a.id)+" in state: "+str(a.currentState),ai)
						
						for ac in actions:
							nextState = a.getTransition(a.currentState, ac)
							qvalues[(nextState, ac)] = a.qvalues[(nextState, ac)]
							if maxq == None:
								maxq = qvalues
								maxActions.append(ac)
							else:
								if qvalues > maxq:
									maxq = qvalues
									maxActions = [ac]
								elif qvalues == maxq:
									maxActions.append(ac)
						otherActions = actions - set(maxActions)
						action = random.choice(maxActions)
						if len(otherActions) > 0:
							if util.flipCoin(self.epsilon):
								action = random.choice(otherActions)
								log.log(str(a.id)+" selected by chance",ai)
													
						nextState = a.getTransition(a.currentState, action)
						a.transit(a.currentState, action)
						reward = a.getReward(a.currentState, action, nextState)
						sample = reward + self.gamma * a.qvalues[(nextState, action)]
						a.qvalues[(a.currentState, action)] = (1-self.alpha) * a.qvalues[(a.currentState, action)] + self.alpha * sample
						
						log.log(str(a.id)+" do: %s \t\t got %f" % (str(action), reward),ai)
						
						if a.terminated:
							activeAgents -= 1
							if a.hiddenState['amountOfCS'] == 0:
								log.log(str(a.id)+" finished successfully -----------------------",3)
							else:
								log.log(str(a.id)+" failed ----------------------- %d" % (a.hiddenState['amountOfCS'],),3)
								
			for a in self.agents:
				a.reset()
				
class Logger:
	def __init__(self, terminalOutput= True, fileOutput=False):
		self.terminalOutput = terminalOutput
		self.fileOutput = fileOutput
		if fileOutput:
			self.file = open('file.log','w')
			
		self.pallet = ['\033[95m','\033[94m','\033[92m','\033[93m','\033[91m']
		self.endc = '\033[0m'
			
	def log(self, message, color=None):
		if self.terminalOutput:
			if color == None:
				print message
			else:
				print self.pallet[color]+message+self.endc
			
		if self.fileOutput:
			self.file.write(str(message)+"\n")