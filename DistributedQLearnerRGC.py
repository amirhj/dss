import random
from DistributedRGCAgent import DistributedRGCAgent
import util
import pprint

class DistributedQLearnerRGC:
	def __init__(self, numberOfAgents, qlearner, sharedModel=False, saveModel=False, loadModel=False, convergence=False, gamma=0.8, alpha=0.9, epsilon=0.1, iteration=500, test=5):
		self.gamma = gamma
		self.alpha = alpha
		self.epsilon = epsilon
		self.iteration = iteration
		self.agents = []
		self.numberOfAgents = numberOfAgents
		self.sharedModel = sharedModel
		self.qlearner = qlearner
		self.test = test
		self.graph = {}
		self.saveModel = saveModel
		self.loadModel = loadModel
		self.convergence = convergence
		
		self.createAgents()
		
		self.globalStateSpace = {}
		self.startStates = set()
		self.startedStates = set()
	
	def createAgents(self):
		qlearner = globals()[str(self.qlearner)]
		
		self.agents = [qlearner(None, None) for i in range(self.numberOfAgents)]
		prevAgent = self.agents[-1]		
		
		for i in range(self.numberOfAgents):
			self.agents[i].id = 'Agent'+str(i)
			self.agents[i].rightN = self.agents[(i+1) % self.numberOfAgents]
			self.agents[i].leftN = prevAgent
			self.agents[i].index = i
			prevAgent = self.agents[i]
			
		if self.sharedModel:
			stateSpace = self.agents[0].qvalues
			if self.loadModel:
				stateSpace = self.loadModel()
			for i in range(1, self.numberOfAgents):
				self.agents[i].qvalues = stateSpace
				
	def run(self):
		log = Logger(False,True)
		for i in range(self.iteration + self.test):
			if i < self.iteration:
				log.log("iteration %d ***************************************" % (i+1,),3)
			else:
				self.turnOffLearning()
				log.log("test %d ***************************************" % (i-self.iteration+1,),3)
			
			lastActions = [None for i in range(self.numberOfAgents)]
			globalState = [None for i in range(self.numberOfAgents)]
			
			while True:
				states = []
				for a in self.agents:
					a.currentState = tuple([random.choice(DistributedRGCAgent.colors) for i in range(3)])
					states.append(a.currentState)
				states = tuple(states)
				if states not in self.startedStates:
					self.startedStates.add(states)
					break
			
			step = 0					
			while not self.isStable(lastActions, globalState):
				step += 1
				agentsSet = set()
				
				agentsColors = []
				for a in self.agents:
					agentsSet.add(a)
					agentsColors.append(a.currentState[0])
				agentsColors = tuple(agentsColors)
				
				if agentsColors not in self.globalStateSpace:
					self.globalStateSpace[agentsColors] = {}
				
				while len(agentsSet) > 0:
					a = random.choice(list(agentsSet))
					agentsSet.remove(a)
					
					
					actions = set(a.getLegalActions(a.currentState))
					qvalues = {}
					maxq = None
					maxActions = []					
					
					log.log(str(a.id)+"\tin state: %s  (%s,%s)" % (str(a.currentState),a.readNeighborColor('right'),a.readNeighborColor('left')),a.index)
						
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
							log.log("\tselected by chance",a.index)
												
					nextState = a.getTransition(a.currentState, action)
					state = a.currentState
					a.transit(a.currentState, action)
					reward = a.getReward(state, action, nextState)
					sample = reward + self.gamma * a.qvalues[(nextState, action)]
					a.qvalues[(state, action)] = (1-self.alpha) * a.qvalues[(state, action)] + self.alpha * sample
					
					
					log.log("\tdo: %s \t got %f" % (str(action), reward),a.index)
					log.log("\tto: %s  (%s,%s)" % (nextState,a.readNeighborColor('right'),a.readNeighborColor('left')),a.index)
					
					if state not in self.graph:
						self.graph[state] = {}
					if action not in self.graph[state]:
						self.graph[state][action] = util.Counter()
					self.graph[state][action][nextState] += 1							
					
					lastActions[a.index] = action
					globalState[a.index] = a.currentState
					
			print "Test episode %d finished in %d clocks." % (i+1, step)
								
			for a in self.agents:
				a.reset()
				
		self.generateGraph()
		
		if self.saveModel:
			self.saveQValues()
			
	def generateGraph(self):
		qvalues = self.agents[0].qvalues
		graph = open('graph.txt', 'w')
		graph.write("digraph markov {\n")
		
		for s in self.graph:
			total = float( sum( sum(self.graph[s][a].values()) for a in self.graph[s] ) )
			for a in self.graph[s]:				
				for ns in self.graph[s][a]:
					prob = self.graph[s][a][ns]/total
					self.graph[s][a][ns] = prob
					graph.write("\t\"%s\" -> \"%s\" [ label = \"%s/%f/%f\"]\n" % (s,ns,a,qvalues[(s,a)], prob))
		
		graph.write("}")
		graph.close()
		
		pprint.pprint(self.graph)
		
	
	def isStable(self, lastActions, agentsState):
		if None in agentsState:
			return False
		actionSet = set(lastActions)
		allGoodAgents = True
		globalState = tuple([a.currentState[0] for a in self.agents])
		for s in agentsState:
			allGoodAgents &= self.isGoodAgentState(s)
		if len(actionSet) == 1 and 'no-action' in actionSet and allGoodAgents and self.isGoodGlobalState(globalState):
			return True
		else:
			return False
		
	def turnOffLearning(self):
		self.alpha = 0
		self.epsilon = 0
		
	def saveQValues(self):
		qvalues = open('QValues.txt', 'w')
		for q in self.agents[0].qvalues:
			s,a = q
			c1,c2,c3 = s
			qvalues.write("%s,%s,%s,%s,%s\n" % (c1,c2,c3,a,str(self.agents[0].qvalues[q])))
		qvalues.close()
		
	def loadQValues(self):
		qvalues = open('QValues.txt', 'r')
		qv = {}
		for line in qvalues:
			v = line.split(',')
			qv[((v[0],v[1],v[2]),v[3])] = v[5]
		return qv
			
	def isGoodGlobalState(self, state):
		for i in range(len(state)-1):
			if state[i] == state[i+1]:
				return False
			
		if state[0] == state[-1]:
			return False
		
		return True
			
	def isGoodAgentState(self, state):
		return state[0] != state[1] and state[0] != state[2]
				
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
				