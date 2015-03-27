import random
from DistributedRGCAgent import DistributedRGCAgent
import util
import pprint
import os
import shutil

class DistributedQLearnerRGCTest:
	def __init__(self, numberOfAgents, qlearner, testName, convergence=False, gamma=0.8, alpha=0.9, epsilon=0.1, tau=8, test=5):
		self.gamma = gamma
		self.alpha = alpha
		self.epsilon = epsilon
		self.tau = tau
		self.agents = []
		self.numberOfAgents = numberOfAgents
		self.qlearner = qlearner
		self.test = test
		self.graph = [ {} for i in range(self.test) ]
		self.convergence = convergence
		self.testName = testName
		
		self.createAgents()
		
		self.globalStateSpace = {}
		self.startStates = set()
		self.startedStates = set()
		self.goodGlobalStates = []
		
		self.palletMap = {'C1':'red', 'C2':'green', 'C3':'blue'}
	
	def createAgents(self):
		qlearner = globals()[str(self.qlearner)]
		
		self.agents = [qlearner(None, None) for i in range(self.numberOfAgents)]
		prevAgent = self.agents[-1]		
		
		self.stateSpace = self.loadQValues()
		
		for i in range(self.numberOfAgents):
			self.agents[i].id = 'Agent'+str(i)
			self.agents[i].rightN = self.agents[(i+1) % self.numberOfAgents]
			self.agents[i].leftN = prevAgent
			self.agents[i].qvalues = self.stateSpace
			self.agents[i].index = i
			prevAgent = self.agents[i]
			
		if os.path.exists('test/'+self.testName):
			shutil.rmtree('test/'+self.testName)
		
		os.mkdir('test/'+self.testName)
				
	def run(self):
		#log = Logger(False,True)
		
		self.turnOffLearning()
		
		for i in range(self.test):
			#log.log("test %d ***************************************" % (i+1,),3)
			
			activityLog = [ [] for k in range(self.numberOfAgents) ]
			
			lastActions = [None for q in range(self.numberOfAgents)]
			globalState = [None for q in range(self.numberOfAgents)]
			
			while True:
				states = []
				for a in self.agents:
					a.currentState = tuple([random.choice(DistributedRGCAgent.colors) for q in range(3)])
					states.append(a.currentState)
				states = tuple(states)
				if states not in self.startedStates:
					self.startedStates.add(states)
					break
				
			# same start state for all agents in all iterations
			for a in self.agents:
				a.currentState = ('C1','C1','C1')	
				
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
					self.globalStateSpace[agentsColors] = util.Counter()
				
				while len(agentsSet) > 0:
					a = random.choice(list(agentsSet))
					agentsSet.remove(a)
					
					actions = set(a.getLegalActions(a.currentState))
					qvalues = {}
					maxq = None
					maxActions = []
					
					activityLog[a.index].append(a.currentState)
					
					#log.log(str(a.id)+"\tin state: %s  (%s,%s)" % (str(a.currentState),a.readNeighborColor('right'),a.readNeighborColor('left')),a.index)
						
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
					
					otherActionQValues = []
					for oc in otherActions:
						for q in qvalues:
							if q[1] == oc:
								otherActionQValues.append(qvalues[q])
					otherActionDistibution = util.softMax(otherActionQValues, self.tau)
					
					action = random.choice(maxActions)
					if len(otherActions) > 0:
						if util.flipCoin(self.epsilon):
							action = util.sample(otherActionDistibution, otherActions)
							#log.log("\tselected by chance",a.index)
												
					nextState = a.getTransition(a.currentState, action)
					state = a.currentState
					a.transit(a.currentState, action)
					reward = a.getReward(state, action, nextState)
					sample = reward + self.gamma * a.qvalues[(nextState, action)]
					a.qvalues[(state, action)] = (1-self.alpha) * a.qvalues[(state, action)] + self.alpha * sample
					
					
					#log.log("\tdo: %s \t got %f" % (str(action), reward),a.index)
					#log.log("\tto: %s  (%s,%s)" % (nextState,a.readNeighborColor('right'),a.readNeighborColor('left')),a.index)
					
					if state not in self.graph[i]:
						self.graph[i][state] = {}
					if action not in self.graph[i][state]:
						self.graph[i][state][action] = util.Counter()
					self.graph[i][state][action][nextState] += 1
					
					lastActions[a.index] = action
					globalState[a.index] = a.currentState
					
					activityLog[a.index].append(action)
					
				agentsNewColors = []
				for a in self.agents:
					agentsNewColors.append(a.currentState[0])
				agentsNewColors = tuple(agentsNewColors)
				
				self.globalStateSpace[agentsColors][agentsNewColors] += 1
			
			print "Test episode %d finished in %d clocks." % (i+1, step)
			
			for a in self.agents:
				activityLog[a.index].append(a.currentState)
				a.reset()
				
			self.generateActivityGraph(activityLog, i+1)
			
		self.generateGraph()
			
	def generateGraph(self):
		graph = open('test/'+self.testName+'/globalState.dot', 'w')
		graph.write("digraph GlobalState {\n\tedge [color=gray, fontColor=black];\n")
		goodStates = set()
		
		for s in self.globalStateSpace:
			total = float( sum( self.globalStateSpace[s].values() ) )
			if self.isGoodGlobalState(s):
				goodStates.add(s)	
			for ns in self.globalStateSpace[s]:
				prob = self.globalStateSpace[s][ns]/total
				self.globalStateSpace[s][ns] = prob
				graph.write("\t\"(%s)\" -> \"(%s)\" [ label = \"%f\" ];\n" % (", ".join(s),", ".join(ns).replace('\'',''), prob))
				if self.isGoodGlobalState(ns):
					goodStates.add(ns)
		
		for g in goodStates:
			graph.write("\t\"(%s)\" [ color=orange ];\n" % (", ".join(g), ) )
		graph.write("}")
		graph.close()
		
		#pprint.pprint(self.graph)
		
	def generateActivityGraph(self, activityLog, iteration):
		path = 'test/'+self.testName+'/test'+str(iteration)
		os.mkdir(path)
						
		j = 0
		for a in activityLog:
			agent = open(path+'/agent'+str(j)+'.dot', 'w')
							
			agent.write("/*\n")
			agent.write(" Agent%d explored states in test episode %d\n" % (j, iteration))
			agent.write(" Finished in %d clocks\n\n" % (len(a)/2,))
			agent.write(" Nodes:\n")
			agent.write(" \tBox: First State\n")
			agent.write(" \tOrange: Good States\n")
			agent.write(" \tRed: Final State\n")
			agent.write(" \tBlue: Bad States\n")
			agent.write(" Edges:\n")
			agent.write(" \t<action>/<number of being taken>\n")
			agent.write(" Actions:\n")
			agent.write(" \tr: Read Right Neighbor's Color\n")
			agent.write(" \tl: Read Left Neighbor's Color\n")
			agent.write(" \tc: Change Color\n")
			agent.write(" \tn: No Action\n")
			agent.write(" Start state: (%s)\n" % (", ".join(a[0]), ))
			agent.write(" Final state: (%s)\n" % (", ".join(a[-1]),))
			agent.write("*/\n")
			agent.write("digraph Agent%d {\n\tedge [color=gray, fontColor=black];\n" % (j,))
			
			goodStates = set()				
			agentPath = set()
			pathCrossing = util.Counter()
			
			i = 0
			while i < len(a)-2:
				agentPath.add((a[i],a[i+1],a[i+2]))
				pathCrossing[(a[i],a[i+1],a[i+2])] += 1			
				
				if self.isGoodAgentState(a[i]):
					goodStates.add(a[i])
				
				i += 2
				
			for p in agentPath:
				#prob = "%s/%.2f/%d" % (self.mapActions(p[1]),self.stateSpace[(p[0],p[1])],pathCrossing[p])
				prob = "%s/%d" % (self.mapActions(p[1]),pathCrossing[p])
				agent.write("\t\"(%s)\" -> \"(%s)\" [ label = \"%s\" ];\n" % (", ".join(p[0]),", ".join(p[2]), prob))
				
			for g in goodStates:
				agent.write("\t\"(%s)\" [ color=orange ];\n" % (", ".join(g), ) )
				
			agent.write("\t\"(%s)\" [ color=red ];\n" % (", ".join(a[-1]), ) )
			agent.write("\t\"(%s)\" [ shape=box ];\n" % (", ".join(a[0]), ) )
							
			agent.write("}")
			agent.close()
			
			j += 1
		
		finalState = open(path+'/final-state.dot', 'w')
		finalState.write("digraph FinalState {\n\tedge [color=gray, fontColor=black];\n")			
		for i in range(self.numberOfAgents-1):
			finalState.write("\t\"A%d\" -- \"A%d\";\n" % (i, i+1))
		finalState.write("\t\"A%d\" -- \"A%d\";\n" % (self.numberOfAgents-1, 0))
		for i in range(self.numberOfAgents):
			finalState.write("\t\"A%d\" [ color=%s ];\n" % (i, self.palletMap[activityLog[i][-1][0]]))
		finalState.write("}")
		finalState.close()
		
	
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
			qv[((v[0],v[1],v[2]),v[3])] = float(v[4])
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
	
	def mapActions(self, action):
		maping = {'changeColor':'c','no-action':'n','read-rn':'r','read-ln':'l'}
		return maping[action]
				
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
				