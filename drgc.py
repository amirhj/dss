# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__ = "amir"
__date__ = "$Mar 10, 2015 6:31:43 PM$"
import DistributedQLearnerRGC
import sys

if __name__ == "__main__":
	keys = {\
		'--episode':{'readValue':True,'default':500, 'name':'episode'},\
		'-t':{'readValue':True,'default':5, 'name':'test'},\
		'--convergence':{'readValue':False,'default':False, 'name':'convergence'},\
		'--gamma':{'readValue':True,'default':0.8, 'name':'gamma'},\
		'--epsilon':{'readValue':True,'default':0.1, 'name':'epsilon'},\
		'--alpha':{'readValue':True,'default':0.9, 'name':'alpha'},\
		'--saveModel':{'readValue':True,'default':True, 'name':'saveModel'},\
		'--loadModel':{'readValue':True,'default':False, 'name':'loadModel'},\
		'--sharedModel':{'readValue':False,'default':True, 'name':'sharedModel'},\
		'-n':{'readValue':True,'default':4, 'name':'n'}\
		}
	
	i = 0
	values = {}
	while i < len(sys.argv):
		key = sys.argv[i]
		if key in keys:
			if keys[key]['readValue']:
				i += 1
				values[keys[key]['name']] = sys.argv[i]
			else:
				values[keys[key]['name']] = keys[key]['default']
		i += 1
		
	for key in keys:
		if keys[key]['name'] not in values:
			values[keys[key]['name']] = keys[key]['default']
		
	print values
	drgc = DistributedQLearnerRGC.DistributedQLearnerRGC(int(values['n']),\
														'DistributedRGCAgent',\
														values['sharedModel'],\
														values['saveModel'],\
														values['loadModel'],\
														values['convergence'],\
														float(values['gamma']),\
														float(values['alpha']),\
														float(values['epsilon']),\
														int(values['episode']),\
														int(values['test']))
	drgc.run()
