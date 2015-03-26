# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__ = "amir"
__date__ = "$Mar 10, 2015 6:31:43 PM$"
import DistributedQLearnerRGCTest
import sys

if __name__ == "__main__":
	keys = {\
		'-t':{'readValue':True,'default':5, 'name':'test'},\
		'--convergence':{'readValue':False,'default':False, 'name':'convergence'},\
		'--gamma':{'readValue':True,'default':0.8, 'name':'gamma'},\
		'--epsilon':{'readValue':True,'default':0.1, 'name':'epsilon'},\
		'--alpha':{'readValue':True,'default':0.9, 'name':'alpha'},\
		'--tau':{'readValue':True,'default':8, 'name':'tau'},\
		'-n':{'readValue':True,'default':4, 'name':'n'}
		}
	
	i = 0
	values = {}
	val = None
	while i < len(sys.argv):
		key = sys.argv[i]
		if key in keys:
			if keys[key]['readValue']:
				i += 1
				values[keys[key]['name']] = sys.argv[i]
			else:
				values[keys[key]['name']] = keys[key]['default']
		else:
			val = key
		i += 1
		
	for key in keys:
		if keys[key]['name'] not in values:
			values[keys[key]['name']] = keys[key]['default']
	values['test-name'] = val
		
	print values
	drgc = DistributedQLearnerRGCTest.DistributedQLearnerRGCTest(int(values['n']),\
														'DistributedRGCAgent',\
														values['test-name'],\
														values['convergence'],\
														float(values['gamma']),\
														float(values['alpha']),\
														float(values['epsilon']),\
														float(values['tau']),\
														int(values['test']))
	drgc.run()
