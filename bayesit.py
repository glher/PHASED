from src.bayesian import BayesianNetwork
from src.model import ModelData
from src.solver import Solver
from src.positions import CombineSensors
import timing
import sys
from collections import OrderedDict


if __name__ == "__main__":
    truncation = True
    details = False
    select = False
    number = 25
    # Solve the model
    # 1 = n, 0 = y (sorry)
    # Diagnostic:
    # evidence = {'Weakness Function 2': 0}
    evidence = {}
    # Optimize:
    #   - Display only critical functions/flows
    #   - Do not print
    display = ['Function 10']
    # Load the data
    model = ModelData()
    model_description = model.load()
    position = CombineSensors(model_description)
    display_final = model_description['nodes']
    states = position.run()
    if len(states) > 5000:
        sys.exit('Probably too long, not gonna bother now')

    ########################################################################################
    # Number of functions and flows
    failure = 2.
    final_state = []
    cnt = 0
    print("{:<20} {:<10}".format('PHM positions', 'Failure of critical function'))
    print("-------------        ----------------------------")
    for state in states:
        cnt += 1
        if select and cnt < number:
            continue
        if select and cnt > number:
            break
        model_description = model.load_phm(model_description, state)
        # Build the model
        bn = BayesianNetwork(model_description)
        bayesian_model = bn.build()
        solver = Solver(bayesian_model, display, evidence)
        e = solver.run(mapquery=False, printed=False)
        if e < failure:
            final_state = state
            failure = e
            print("{:<20} {:.4E} *".format(cnt, e))
        else:
            print("{:<20} {:.4E}".format(cnt, e))
    if details:
        print('\n=====================\n')
        model_description = model.load_phm(model_description, final_state)
        # Build the model
        bn = BayesianNetwork(model_description)
        bayesian_model = bn.build()
        solver = Solver(bayesian_model, display_final, evidence)
        e = solver.run(mapquery=False, printed=True)
        print('\n=====================\n')

    final_state = OrderedDict(zip(model_description['nodes'], final_state))
    print("{:<15} {:<10}".format('Function', 'Sensor'))
    print("--------------- ----------")
    for k, v in iter(final_state.items()):
        print("{:<15} {:<10}".format(k, v))
    print("--------------- ----------")
    print('\nFinal failure rate of %s (sum): %.4E \n' % (display, failure))
