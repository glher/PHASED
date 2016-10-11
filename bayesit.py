from src.bayesian import BayesianNetwork
from src.model import ModelData
from src.solver import Solver
import timing

if __name__ == "__main__":

    # Load the data
    model = ModelData()
    model_description = model.load()
    # Build the model
    bn = BayesianNetwork(model_description)
    bayesian_model = bn.build()
    # Solve the model
    evidence = {'Weakness Function 1': 0, 'Weakness Function 2': 0, 'Weakness Boundary input': 1}
    display = ['Boundary input',
               'Flow b;1',
               'Function 1',
               'Flow 1;2',
               'Function 2',
               'Flow 2;3',
               'Function 3',
               'Flow b;4',
               'Function 4',
               'Flow 4;g1',
               'Flow 2;g1',
               'Gate 1 f2-f4',
               'Flow 3;10',
               'Function 10']
    solver = Solver(bayesian_model, display, evidence)
    solver.run()
