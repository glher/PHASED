from src.bayesian import BayesianNetwork
from src.model import ModelData
from src.solver import Solver
import timing

import itertools
import numpy as np
from collections import OrderedDict


if __name__ == "__main__":
    # Solve the model
    evidence = {'Weakness Boundary input': 1}
    # Optimize:
    #   - Display only critical functions/flows
    #   - Do not print
    display = [
               # 'Boundary input',
               # 'Flow b;1',
               'Function 1',
               # 'Flow 1;2',
               'Function 2',
               # 'Flow 2;3',
               # 'Function 3',
               # 'Flow b;4',
               # 'Function 4',
               # 'Flow 4;g1',
               # 'Flow 2;g1',
               # 'Gate 1 f2-f4',
               # 'Flow 3;10',
               # 'Function 10'
               ]
    # Load the data
    model = ModelData()
    model_description = model.load()
    # Number of functions and flows
    cnt = 0
    idx_nosensor = {}
    exception_sensors = {'Boundary': '0', 'Gate': '0'}
    for i, n in enumerate(model_description['nodes']):
        for e in exception_sensors:
            if e in n:
                idx_nosensor[i] = exception_sensors[e]
        cnt += 1
    # Given inventory
    inventory = {'phm_1': 3, 'phm_2': 1}
    state = []
    inventory_list = list(inventory.keys()) + [0]

    states = np.array([p for p in itertools.product(inventory_list, repeat=cnt)])
    for v in inventory:
        delete = np.where(states == v)[0]
        idx = np.where(np.bincount(delete) > inventory[v])
        states = np.delete(states, idx, axis=0)
    for i in idx_nosensor:
        states = states[states[:, i] == idx_nosensor[i]]

    failure = 1.
    final_state = []
    print('Number of possible permutations: %s' % len(states))
    for state in states:
        print(state)
        model_description = model.load_phm(model_description, state)
        # Build the model
        bn = BayesianNetwork(model_description)
        bayesian_model = bn.build()
        solver = Solver(bayesian_model, display, evidence)
        e = solver.run(mapquery=False)
        if e < failure:
            final_state = state
            failure = e
        print(e)
    final_state = OrderedDict(zip(model_description['nodes'], final_state))
    print("{:<15} {:<10}".format('Function', 'Sensor'))
    print("--------------- ----------")
    for k, v in iter(final_state.items()):
        print("{:<15} {:<10}".format(k, v))
    print("--------------- ----------")
    print('\nFinal failure rate of %s (sum): %.4E \n' % (display, failure))
