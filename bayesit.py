from src.bayesian import BayesianNetwork
from src.model import ModelData
from src.solver import Solver
from src.positions import CombineSensors
import timing
import sys
from collections import OrderedDict


if __name__ == "__main__":
    truncation = True
    # Solve the model
    # 1 = n, 0 = y (sorry)
    evidence = {'Weakness Function 2': 0}
    # evidence = {'Weakness Function 5': 1}
    # Optimize:
    #   - Display only critical functions/flows
    #   - Do not print
    display = [
               # 'Boundary input',
               # 'Flow b;1',
               #'Function 1',
               # 'Flow 1;2',
               # 'Function 2',
               # 'Flow 2;3',
               # 'Function 3',
               # 'Flow b;4',
               # 'Function 4',
               # 'Flow 4;g1',
               # 'Flow 2;g1',
               # 'Gate 1 f2-f4',
               # 'Flow 3;10',
               'Function 10'
               ]
    # Load the data
    model = ModelData()
    model_description = model.load()

    position = CombineSensors(model_description)
    states = position.run()
    if len(states) > 5000:
        sys.exit('Probably too long, not gonna bother now')

    ########################################################################################
    # Number of functions and flows
    failure = 2.
    final_state = []
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
